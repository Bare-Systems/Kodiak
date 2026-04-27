"""Tests for portfolio analytics calculations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pandas as pd
from kodiak.analysis.portfolio import (
    SNAPSHOT_METHODOLOGY,
    TRANSACTION_METHODOLOGY,
    compute_portfolio_analytics,
    compute_transaction_portfolio_analytics,
)
from kodiak.api.broker import Account, OrderSide, OrderStatus, Position
from kodiak.data.ledger import TradeRecord
from kodiak.schemas.portfolio import PortfolioAnalyticsResponse


def _history(values: list[float]) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=len(values), freq="D", tz="US/Eastern")
    return pd.DataFrame(
        {
            "open": values,
            "high": values,
            "low": values,
            "close": values,
            "volume": [1_000_000] * len(values),
        },
        index=index,
    )


class TestComputePortfolioAnalytics:
    """Test snapshot-based analytics calculations."""

    def test_computes_returns_drawdown_and_exposure(self) -> None:
        account = Account(
            cash=Decimal("1000"),
            buying_power=Decimal("5000"),
            equity=Decimal("3200"),
            portfolio_value=Decimal("3200"),
        )
        positions = [
            Position(
                symbol="AAPL",
                qty=Decimal("10"),
                avg_entry_price=Decimal("100"),
                current_price=Decimal("110"),
                market_value=Decimal("1100"),
                unrealized_pl=Decimal("100"),
                unrealized_pl_pct=Decimal("0.10"),
            ),
            Position(
                symbol="MSFT",
                qty=Decimal("5"),
                avg_entry_price=Decimal("200"),
                current_price=Decimal("220"),
                market_value=Decimal("1100"),
                unrealized_pl=Decimal("100"),
                unrealized_pl_pct=Decimal("0.10"),
            ),
        ]

        result = compute_portfolio_analytics(
            account=account,
            positions=positions,
            price_history={
                "AAPL": _history([100, 101, 103, 102, 108, 110]),
                "MSFT": _history([200, 201, 202, 210, 215, 220]),
                "SPY": _history([400, 402, 404, 403, 410, 420]),
            },
            benchmark_symbol="SPY",
            data_source="csv",
            lookback_days=5,
            generated_at=datetime(2026, 4, 23, 9, 30, 0),
        )

        assert result.benchmark_symbol == "SPY"
        assert result.methodology == SNAPSHOT_METHODOLOGY
        assert result.position_count == 2
        assert result.trading_days == 5
        assert result.cumulative_return_pct > Decimal("0")
        assert result.max_drawdown_pct >= Decimal("0")
        assert result.exposure.gross_exposure == Decimal("2200")
        assert result.exposure.cash_weight_pct > Decimal("0")
        assert result.sharpe_ratio is not None
        assert len(result.rolling_returns) == 5
        assert result.constituents[0].symbol == "AAPL"
        assert len(result.equity_curve) == 6
        assert result.equity_curve[-1].equity == Decimal("3200.000000")

    def test_handles_cash_only_portfolio(self) -> None:
        account = Account(
            cash=Decimal("5000"),
            buying_power=Decimal("5000"),
            equity=Decimal("5000"),
            portfolio_value=Decimal("5000"),
        )

        result = compute_portfolio_analytics(
            account=account,
            positions=[],
            price_history={"SPY": _history([400, 401, 402, 405])},
            benchmark_symbol="SPY",
            data_source="csv",
            lookback_days=3,
            generated_at=datetime(2026, 4, 23, 9, 30, 0),
        )

        assert result.cumulative_return_pct == Decimal("0.000000")
        assert result.max_drawdown_pct == Decimal("0.000000")
        assert result.exposure.cash_weight_pct == Decimal("100")
        assert result.sharpe_ratio is None
        assert result.equity_curve[-1].cash == Decimal("5000.000000")

    def test_reconstructs_transaction_level_equity_curve(self) -> None:
        account = Account(
            cash=Decimal("9400"),
            buying_power=Decimal("9400"),
            equity=Decimal("10600"),
            portfolio_value=Decimal("10600"),
        )
        positions = [
            Position(
                symbol="AAPL",
                qty=Decimal("10"),
                avg_entry_price=Decimal("100"),
                current_price=Decimal("120"),
                market_value=Decimal("1200"),
                unrealized_pl=Decimal("200"),
                unrealized_pl_pct=Decimal("0.20"),
            )
        ]
        trades = [
            TradeRecord(
                id=1,
                order_id="buy-aapl",
                symbol="AAPL",
                side=OrderSide.BUY.value,
                quantity=Decimal("10"),
                price=Decimal("100"),
                total=Decimal("1000"),
                status=OrderStatus.FILLED.value,
                rule_id=None,
                timestamp=datetime(2024, 1, 3, 10, 0, 0),
            )
        ]

        result = compute_transaction_portfolio_analytics(
            account=account,
            positions=positions,
            trades=trades,
            price_history={
                "AAPL": _history([90, 95, 100, 110, 120]),
                "SPY": _history([400, 401, 402, 403, 404]),
            },
            benchmark_symbol="SPY",
            data_source="csv",
            lookback_days=4,
            generated_at=datetime(2026, 4, 26, 9, 30, 0),
        )

        assert result.methodology == TRANSACTION_METHODOLOGY
        assert result.equity_curve[0].equity == Decimal("10400.000000")
        assert result.equity_curve[0].cash == Decimal("10400.000000")
        assert result.equity_curve[2].equity == Decimal("10400.000000")
        assert result.equity_curve[2].cash == Decimal("9400.000000")
        assert result.equity_curve[-1].equity == Decimal("10600.000000")
        assert result.cumulative_return_pct == Decimal("1.923077")
        assert result.constituents[0].period_return_pct == Decimal("20.000000")
        assert result.constituents[0].contribution_pct == Decimal("1.923077")
        assert result.attribution[0].group_by in {"symbol", "rule", "strategy"}

    def test_response_includes_equity_curve(self) -> None:
        account = Account(
            cash=Decimal("5000"),
            buying_power=Decimal("5000"),
            equity=Decimal("5000"),
            portfolio_value=Decimal("5000"),
        )
        result = compute_portfolio_analytics(
            account=account,
            positions=[],
            price_history={"SPY": _history([400, 401, 402])},
            benchmark_symbol="SPY",
            data_source="csv",
            lookback_days=2,
            generated_at=datetime(2026, 4, 26, 9, 30, 0),
        )

        response = PortfolioAnalyticsResponse.from_domain(result)

        assert len(response.equity_curve) == 3
        assert response.equity_curve[0].equity == Decimal("5000.000000")
        assert response.attribution == []

    def test_attributes_performance_by_symbol_rule_and_strategy(self) -> None:
        account = Account(
            cash=Decimal("9575"),
            buying_power=Decimal("9575"),
            equity=Decimal("10175"),
            portfolio_value=Decimal("10175"),
        )
        positions = [
            Position(
                symbol="AAPL",
                qty=Decimal("5"),
                avg_entry_price=Decimal("100"),
                current_price=Decimal("120"),
                market_value=Decimal("600"),
                unrealized_pl=Decimal("100"),
                unrealized_pl_pct=Decimal("0.20"),
            )
        ]
        trades = [
            TradeRecord(
                id=1,
                order_id="buy-aapl",
                symbol="AAPL",
                side=OrderSide.BUY.value,
                quantity=Decimal("10"),
                price=Decimal("100"),
                total=Decimal("1000"),
                status=OrderStatus.FILLED.value,
                rule_id="strategy-a:entry",
                timestamp=datetime(2024, 1, 3, 10, 0, 0),
            ),
            TradeRecord(
                id=2,
                order_id="sell-aapl",
                symbol="AAPL",
                side=OrderSide.SELL.value,
                quantity=Decimal("5"),
                price=Decimal("115"),
                total=Decimal("575"),
                status=OrderStatus.FILLED.value,
                rule_id="strategy-a:exit",
                timestamp=datetime(2024, 1, 5, 10, 0, 0),
            ),
        ]

        result = compute_transaction_portfolio_analytics(
            account=account,
            positions=positions,
            trades=trades,
            price_history={
                "AAPL": _history([90, 95, 100, 110, 120]),
                "SPY": _history([400, 401, 402, 403, 404]),
            },
            benchmark_symbol="SPY",
            data_source="csv",
            lookback_days=4,
            generated_at=datetime(2026, 4, 26, 9, 30, 0),
        )

        by_group = {(item.group_by, item.key): item for item in result.attribution}
        symbol = by_group[("symbol", "AAPL")]
        rule = by_group[("rule", "strategy-a:entry")]
        strategy = by_group[("strategy", "strategy-a")]

        assert symbol.realized_pnl == Decimal("75")
        assert symbol.unrealized_pnl == Decimal("100")
        assert symbol.total_pnl == Decimal("175")
        assert symbol.contribution_pct == Decimal("1.750000")
        assert symbol.trade_count == 2
        assert symbol.buy_qty == Decimal("10")
        assert symbol.sell_qty == Decimal("5")

        assert rule.realized_pnl == Decimal("75")
        assert rule.unrealized_pnl == Decimal("100")
        assert rule.total_pnl == Decimal("175")
        assert rule.buy_qty == Decimal("10")
        assert rule.sell_qty == Decimal("5")

        assert strategy.total_pnl == Decimal("175")
        assert strategy.contribution_pct == Decimal("1.750000")
