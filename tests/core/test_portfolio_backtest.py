"""Tests for portfolio-level multi-symbol backtesting."""

from decimal import Decimal

import pandas as pd
import pytest
from kodiak.schemas.backtests import (
    BacktestRequest,
    BacktestResponse,
    PortfolioBacktestResponse,
    PortfolioSymbolSummary,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_csv_data(symbol: str, price: float = 100.0, num_bars: int = 50) -> pd.DataFrame:
    timestamps = pd.date_range("2024-01-02", periods=num_bars, freq="B")
    return pd.DataFrame(
        {
            "open": price,
            "high": price * 1.02,
            "low": price * 0.98,
            "close": price,
            "volume": 500000,
        },
        index=timestamps,
    )


def _make_multi_symbol_request(
    symbols: list[str],
    initial_capital: float = 10000.0,
) -> BacktestRequest:
    return BacktestRequest(
        strategy_type="trailing-stop",
        symbols=symbols,
        start="2024-01-01",
        end="2024-12-31",
        trailing_pct=5.0,
        initial_capital=initial_capital,
        save=False,
    )


# ---------------------------------------------------------------------------
# BacktestRequest schema tests
# ---------------------------------------------------------------------------


class TestBacktestRequestSchema:
    def test_single_symbol_via_symbol_field(self) -> None:
        req = BacktestRequest(
            strategy_type="trailing-stop",
            symbol="aapl",
            start="2024-01-01",
            end="2024-12-31",
            trailing_pct=5.0,
        )
        assert req.get_symbols() == ["AAPL"]

    def test_single_symbol_via_symbols_list(self) -> None:
        req = BacktestRequest(
            strategy_type="trailing-stop",
            symbols=["msft"],
            start="2024-01-01",
            end="2024-12-31",
            trailing_pct=5.0,
        )
        assert req.get_symbols() == ["MSFT"]

    def test_multi_symbol_list(self) -> None:
        req = _make_multi_symbol_request(["AAPL", "MSFT", "GOOGL"])
        assert req.get_symbols() == ["AAPL", "MSFT", "GOOGL"]

    def test_symbols_uppercased(self) -> None:
        req = BacktestRequest(
            strategy_type="trailing-stop",
            symbols=["aapl", "msft"],
            start="2024-01-01",
            end="2024-12-31",
            trailing_pct=5.0,
        )
        assert req.get_symbols() == ["AAPL", "MSFT"]

    def test_no_symbol_raises(self) -> None:
        with pytest.raises(Exception):
            BacktestRequest(
                strategy_type="trailing-stop",
                start="2024-01-01",
                end="2024-12-31",
                trailing_pct=5.0,
            )

    def test_symbols_takes_precedence_when_both_set(self) -> None:
        req = BacktestRequest(
            strategy_type="trailing-stop",
            symbol="AAPL",
            symbols=["MSFT", "GOOGL"],
            start="2024-01-01",
            end="2024-12-31",
            trailing_pct=5.0,
        )
        assert req.get_symbols() == ["MSFT", "GOOGL"]

    def test_legacy_symbol_backward_compat(self) -> None:
        """Single-symbol requests using the old `symbol` field must still work."""
        req = BacktestRequest(
            strategy_type="bracket",
            symbol="TSLA",
            start="2024-01-01",
            end="2024-12-31",
            take_profit=0.05,
            stop_loss=0.02,
        )
        assert req.get_symbols() == ["TSLA"]
        assert req.symbol == "TSLA"


# ---------------------------------------------------------------------------
# Portfolio orchestration tests (using app layer with patched broker)
# ---------------------------------------------------------------------------


class TestPortfolioBacktest:
    def test_multi_symbol_returns_portfolio_response(self, tmp_path, monkeypatch) -> None:
        """_run_portfolio_backtest returns PortfolioBacktestResponse for 2+ symbols."""
        from kodiak.app.backtests import _run_portfolio_backtest
        from kodiak.utils.config import Config, Environment, Service, StrategyDefaults
        config = Config(
            env=Environment.PAPER,
            service=Service.ALPACA,
            alpaca_api_key="",
            alpaca_secret_key="",
            base_url="https://paper-api.alpaca.markets",
            data_dir=tmp_path,
            log_dir=tmp_path,
            strategy_defaults=StrategyDefaults(),
        )
        symbols = ["AAPL", "MSFT"]

        # Patch _run_single_symbol_backtest to avoid file I/O
        def fake_single(cfg, req, sym):
            return BacktestResponse(
                id=sym[:4].lower(),
                strategy_type="trailing-stop",
                symbol=sym,
                start_date="2024-01-02T00:00:00",
                end_date="2024-12-31T00:00:00",
                created_at="2024-12-31T00:00:00",
                strategy_config={},
                initial_capital=Decimal("5000"),
                total_return=Decimal("250"),
                total_return_pct=Decimal("5"),
                win_rate=Decimal("60"),
                profit_factor=Decimal("1.5"),
                max_drawdown=Decimal("100"),
                max_drawdown_pct=Decimal("2"),
                total_fees_paid=Decimal("10"),
                gross_return=Decimal("260"),
                gross_return_pct=Decimal("5.2"),
                total_trades=10,
                winning_trades=6,
                losing_trades=4,
            )

        import kodiak.app.backtests as bt_mod
        monkeypatch.setattr(bt_mod, "_run_single_symbol_backtest", fake_single)

        req = _make_multi_symbol_request(symbols, initial_capital=10000.0)
        result = _run_portfolio_backtest(config, req, symbols)

        assert isinstance(result, PortfolioBacktestResponse)
        assert result.symbols == symbols
        assert len(result.symbol_results) == 2
        assert len(result.symbol_attribution) == 2

    def test_portfolio_capital_split_equally(self, tmp_path, monkeypatch) -> None:
        from kodiak.app.backtests import _run_portfolio_backtest
        from kodiak.utils.config import Config, Environment, Service, StrategyDefaults
        config = Config(
            env=Environment.PAPER,
            service=Service.ALPACA,
            alpaca_api_key="",
            alpaca_secret_key="",
            base_url="https://paper-api.alpaca.markets",
            data_dir=tmp_path,
            log_dir=tmp_path,
            strategy_defaults=StrategyDefaults(),
        )
        captured_capitals = []

        def fake_single(cfg, req, sym):
            captured_capitals.append(float(req.initial_capital))
            return BacktestResponse(
                id=sym[:4].lower(),
                strategy_type="trailing-stop",
                symbol=sym,
                start_date="2024-01-02T00:00:00",
                end_date="2024-12-31T00:00:00",
                created_at="2024-12-31T00:00:00",
                strategy_config={},
                initial_capital=Decimal(str(req.initial_capital)),
                total_return=Decimal("0"),
                total_return_pct=Decimal("0"),
                win_rate=Decimal("0"),
                profit_factor=Decimal("0"),
                max_drawdown=Decimal("0"),
                max_drawdown_pct=Decimal("0"),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
            )

        import kodiak.app.backtests as bt_mod
        monkeypatch.setattr(bt_mod, "_run_single_symbol_backtest", fake_single)

        req = _make_multi_symbol_request(["AAPL", "MSFT", "GOOGL"], initial_capital=30000.0)
        _run_portfolio_backtest(config, req, ["AAPL", "MSFT", "GOOGL"])

        assert len(captured_capitals) == 3
        assert all(abs(c - 10000.0) < 0.01 for c in captured_capitals)

    def test_portfolio_metrics_aggregation(self, tmp_path, monkeypatch) -> None:
        from kodiak.app.backtests import _run_portfolio_backtest
        from kodiak.utils.config import Config, Environment, Service, StrategyDefaults
        config = Config(
            env=Environment.PAPER,
            service=Service.ALPACA,
            alpaca_api_key="",
            alpaca_secret_key="",
            base_url="https://paper-api.alpaca.markets",
            data_dir=tmp_path,
            log_dir=tmp_path,
            strategy_defaults=StrategyDefaults(),
        )
        responses = [
            BacktestResponse(
                id="aapl",
                strategy_type="trailing-stop",
                symbol="AAPL",
                start_date="2024-01-02T00:00:00",
                end_date="2024-12-31T00:00:00",
                created_at="2024-12-31T00:00:00",
                strategy_config={},
                initial_capital=Decimal("5000"),
                total_return=Decimal("500"),
                total_return_pct=Decimal("10"),
                win_rate=Decimal("70"),
                profit_factor=Decimal("2"),
                max_drawdown=Decimal("200"),
                max_drawdown_pct=Decimal("4"),
                total_fees_paid=Decimal("20"),
                gross_return=Decimal("520"),
                gross_return_pct=Decimal("10.4"),
                total_trades=10,
                winning_trades=7,
                losing_trades=3,
            ),
            BacktestResponse(
                id="msft",
                strategy_type="trailing-stop",
                symbol="MSFT",
                start_date="2024-01-02T00:00:00",
                end_date="2024-12-31T00:00:00",
                created_at="2024-12-31T00:00:00",
                strategy_config={},
                initial_capital=Decimal("5000"),
                total_return=Decimal("-100"),
                total_return_pct=Decimal("-2"),
                win_rate=Decimal("40"),
                profit_factor=Decimal("0.8"),
                max_drawdown=Decimal("300"),
                max_drawdown_pct=Decimal("6"),
                total_fees_paid=Decimal("15"),
                gross_return=Decimal("-85"),
                gross_return_pct=Decimal("-1.7"),
                total_trades=5,
                winning_trades=2,
                losing_trades=3,
            ),
        ]
        iter_results = iter(responses)

        import kodiak.app.backtests as bt_mod
        monkeypatch.setattr(bt_mod, "_run_single_symbol_backtest", lambda cfg, req, sym: next(iter_results))

        req = _make_multi_symbol_request(["AAPL", "MSFT"], initial_capital=10000.0)
        result = _run_portfolio_backtest(config, req, ["AAPL", "MSFT"])

        # Portfolio return = average of +10% and -2% = 4%
        assert result.portfolio_return_pct == Decimal("4")
        # Total fees = 20 + 15 = 35
        assert result.portfolio_total_fees_paid == Decimal("35")
        # Max drawdown = max(4%, 6%) = 6%
        assert result.portfolio_max_drawdown_pct == Decimal("6")
        # Total trades = 10 + 5 = 15
        assert result.total_trades == 15
        # Win rate = (7 + 2) / 15 * 100 = 60%
        assert abs(float(result.portfolio_win_rate) - 60.0) < 0.01

    def test_attribution_has_all_symbols(self, tmp_path, monkeypatch) -> None:
        from kodiak.app.backtests import _run_portfolio_backtest
        from kodiak.utils.config import Config, Environment, Service, StrategyDefaults
        config = Config(
            env=Environment.PAPER,
            service=Service.ALPACA,
            alpaca_api_key="",
            alpaca_secret_key="",
            base_url="https://paper-api.alpaca.markets",
            data_dir=tmp_path,
            log_dir=tmp_path,
            strategy_defaults=StrategyDefaults(),
        )
        symbols = ["AAPL", "MSFT", "TSLA"]

        def fake_single(cfg, req, sym):
            return BacktestResponse(
                id=sym[:4].lower(),
                strategy_type="trailing-stop",
                symbol=sym,
                start_date="2024-01-02T00:00:00",
                end_date="2024-12-31T00:00:00",
                created_at="2024-12-31T00:00:00",
                strategy_config={},
                initial_capital=Decimal("3333.33"),
                total_return=Decimal("0"),
                total_return_pct=Decimal("0"),
                win_rate=Decimal("0"),
                profit_factor=Decimal("0"),
                max_drawdown=Decimal("0"),
                max_drawdown_pct=Decimal("0"),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
            )

        import kodiak.app.backtests as bt_mod
        monkeypatch.setattr(bt_mod, "_run_single_symbol_backtest", fake_single)

        req = _make_multi_symbol_request(symbols)
        result = _run_portfolio_backtest(config, req, symbols)

        attr_symbols = [a.symbol for a in result.symbol_attribution]
        assert attr_symbols == symbols
        for attr in result.symbol_attribution:
            assert isinstance(attr, PortfolioSymbolSummary)


# ---------------------------------------------------------------------------
# Schema field tests
# ---------------------------------------------------------------------------


class TestPortfolioSchemas:
    def test_portfolio_response_fields(self) -> None:
        fields = PortfolioBacktestResponse.model_fields
        required_fields = {
            "id", "strategy_type", "symbols", "start_date", "end_date", "created_at",
            "initial_capital", "portfolio_return_pct", "portfolio_gross_return_pct",
            "portfolio_total_fees_paid", "portfolio_max_drawdown_pct", "portfolio_win_rate",
            "total_trades", "symbol_results", "symbol_attribution",
        }
        for field in required_fields:
            assert field in fields, f"Missing field: {field}"

    def test_portfolio_symbol_summary_fields(self) -> None:
        fields = PortfolioSymbolSummary.model_fields
        required = {
            "symbol", "backtest_id", "allocation", "total_return", "total_return_pct",
            "gross_return_pct", "total_fees_paid", "win_rate", "total_trades", "max_drawdown_pct",
        }
        for field in required:
            assert field in fields, f"Missing field: {field}"
