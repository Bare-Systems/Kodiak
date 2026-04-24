"""Tests for position sizing and rebalance planning."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from kodiak.analysis.allocation import calculate_position_size, generate_rebalance_plan
from kodiak.api.broker import Account, Position


def _account() -> Account:
    return Account(
        cash=Decimal("10000"),
        buying_power=Decimal("15000"),
        equity=Decimal("20000"),
        portfolio_value=Decimal("20000"),
    )


class TestCalculatePositionSize:
    """Test sizing primitives."""

    def test_target_weight_sizing(self) -> None:
        result = calculate_position_size(
            symbol="AAPL",
            method="target_weight",
            reference_price=Decimal("100"),
            account=_account(),
            current_qty=Decimal("10"),
            target_weight_pct=Decimal("15"),
            lot_size=1,
            generated_at=datetime(2026, 4, 23, 10, 0, 0),
        )
        assert result.target_qty == Decimal("30")
        assert result.delta_qty == Decimal("20")
        assert result.target_position_value == Decimal("3000")

    def test_risk_budget_sizing_applies_caps(self) -> None:
        result = calculate_position_size(
            symbol="NVDA",
            method="risk_budget",
            reference_price=Decimal("200"),
            account=_account(),
            current_qty=Decimal("0"),
            risk_budget=Decimal("1000"),
            stop_loss_pct=Decimal("5"),
            max_position_weight_pct=Decimal("10"),
            lot_size=1,
        )
        assert result.target_qty == Decimal("10")
        assert "max_position_weight_pct" in result.capped_by

    def test_invalid_method_raises(self) -> None:
        with pytest.raises(ValueError):
            calculate_position_size(
                symbol="AAPL",
                method="unknown",
                reference_price=Decimal("100"),
                account=_account(),
            )


class TestGenerateRebalancePlan:
    """Test rebalance planning."""

    def test_generates_sell_then_buy_plan(self) -> None:
        plan = generate_rebalance_plan(
            account=_account(),
            current_positions=[
                Position(
                    symbol="AAPL",
                    qty=Decimal("50"),
                    avg_entry_price=Decimal("90"),
                    current_price=Decimal("100"),
                    market_value=Decimal("5000"),
                    unrealized_pl=Decimal("500"),
                    unrealized_pl_pct=Decimal("0.11"),
                ),
                Position(
                    symbol="MSFT",
                    qty=Decimal("10"),
                    avg_entry_price=Decimal("200"),
                    current_price=Decimal("200"),
                    market_value=Decimal("2000"),
                    unrealized_pl=Decimal("0"),
                    unrealized_pl_pct=Decimal("0"),
                ),
            ],
            target_weights={"AAPL": Decimal("10"), "MSFT": Decimal("20"), "NVDA": Decimal("15")},
            reference_prices={"NVDA": Decimal("250")},
            drift_threshold_pct=Decimal("1"),
            cash_buffer_pct=Decimal("5"),
            liquidate_unmentioned=False,
            lot_size=1,
            generated_at=datetime(2026, 4, 23, 10, 0, 0),
        )
        assert plan.rebalance_required is True
        assert plan.trade_count == 3
        assert plan.trades[0].side == "sell"
        assert {trade.symbol for trade in plan.trades} == {"AAPL", "MSFT", "NVDA"}

    def test_liquidates_unmentioned_positions(self) -> None:
        plan = generate_rebalance_plan(
            account=_account(),
            current_positions=[
                Position(
                    symbol="XLP",
                    qty=Decimal("20"),
                    avg_entry_price=Decimal("80"),
                    current_price=Decimal("80"),
                    market_value=Decimal("1600"),
                    unrealized_pl=Decimal("0"),
                    unrealized_pl_pct=Decimal("0"),
                )
            ],
            target_weights={},
            reference_prices={},
            liquidate_unmentioned=True,
            drift_threshold_pct=Decimal("1"),
        )
        assert plan.trade_count == 1
        assert plan.trades[0].symbol == "XLP"
        assert plan.trades[0].side == "sell"

    def test_cash_buffer_violation_raises(self) -> None:
        with pytest.raises(ValueError):
            generate_rebalance_plan(
                account=_account(),
                current_positions=[],
                target_weights={"NVDA": Decimal("95")},
                reference_prices={"NVDA": Decimal("100")},
                cash_buffer_pct=Decimal("10"),
            )
