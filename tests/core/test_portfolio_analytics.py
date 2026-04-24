"""Tests for portfolio analytics calculations."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pandas as pd
from kodiak.analysis.portfolio import compute_portfolio_analytics
from kodiak.api.broker import Account, Position


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
        assert result.position_count == 2
        assert result.trading_days == 5
        assert result.cumulative_return_pct > Decimal("0")
        assert result.max_drawdown_pct >= Decimal("0")
        assert result.exposure.gross_exposure == Decimal("2200")
        assert result.exposure.cash_weight_pct > Decimal("0")
        assert result.sharpe_ratio is not None
        assert len(result.rolling_returns) == 5
        assert result.constituents[0].symbol == "AAPL"

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
