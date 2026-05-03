"""Tests for execution realism models: fees, slippage, and partial fills."""

from decimal import Decimal

import pandas as pd
import pytest
from kodiak.api.broker import OrderSide, OrderStatus, OrderType
from kodiak.backtest.broker import HistoricalBroker
from kodiak.schemas.backtests import (
    BacktestRequest,
    BacktestResponse,
    ExecutionConfig,
    FeeModel,
    FillModel,
    SlippageModel,
)
from kodiak.schemas.optimization import OptimizeRequest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_broker(
    price: float = 100.0,
    num_bars: int = 5,
    execution_config: ExecutionConfig | None = None,
    initial_cash: float = 100000.0,
) -> HistoricalBroker:
    """Build a minimal HistoricalBroker with synthetic OHLCV data."""
    timestamps = pd.date_range("2024-01-02", periods=num_bars, freq="B")
    df = pd.DataFrame(
        {
            "open": price,
            "high": price * 1.01,
            "low": price * 0.99,
            "close": price,
            "volume": 100000,
        },
        index=timestamps,
    )
    return HistoricalBroker(
        historical_data={"AAPL": df},
        initial_cash=Decimal(str(initial_cash)),
        execution_config=execution_config,
    )


# ---------------------------------------------------------------------------
# Fee model tests
# ---------------------------------------------------------------------------


class TestFeeModel:
    def test_no_fee_default(self) -> None:
        broker = _make_broker()
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        initial_cash = broker._account.cash

        broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)

        expected_cost = Decimal("10") * Decimal("100")
        assert broker._account.cash == initial_cash - expected_cost
        assert broker.total_fees == Decimal("0")

    def test_fixed_fee_per_order(self) -> None:
        fee_per_order = Decimal("1.00")
        config = ExecutionConfig(fee=FeeModel(type="fixed", value=float(fee_per_order)))
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        initial_cash = broker._account.cash

        broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)

        notional = Decimal("10") * Decimal("100")
        assert broker._account.cash == initial_cash - notional - fee_per_order
        assert broker.total_fees == fee_per_order

    def test_percentage_fee(self) -> None:
        fee_fraction = 0.001  # 0.1%
        config = ExecutionConfig(fee=FeeModel(type="percentage", value=fee_fraction))
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        initial_cash = broker._account.cash

        broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)

        notional = Decimal("10") * Decimal("100")
        expected_fee = notional * Decimal(str(fee_fraction))
        assert broker._account.cash == initial_cash - notional - expected_fee
        assert broker.total_fees == expected_fee

    def test_fees_accumulate_across_orders(self) -> None:
        config = ExecutionConfig(fee=FeeModel(type="fixed", value=2.0))
        broker = _make_broker(execution_config=config)

        broker.advance_to_bar(broker.data["AAPL"].index[0])
        broker.place_order("AAPL", Decimal("5"), OrderSide.BUY, OrderType.MARKET)

        broker.advance_to_bar(broker.data["AAPL"].index[1])
        broker.place_order("AAPL", Decimal("5"), OrderSide.SELL, OrderType.MARKET)

        assert broker.total_fees == Decimal("4.00")  # 2 orders × $2

    def test_sell_fee_reduces_proceeds(self) -> None:
        config = ExecutionConfig(fee=FeeModel(type="fixed", value=5.0))
        broker = _make_broker(execution_config=config)

        broker.advance_to_bar(broker.data["AAPL"].index[0])
        broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)
        cash_after_buy = broker._account.cash

        broker.advance_to_bar(broker.data["AAPL"].index[1])
        broker.place_order("AAPL", Decimal("10"), OrderSide.SELL, OrderType.MARKET)
        cash_after_sell = broker._account.cash

        notional = Decimal("10") * Decimal("100")
        # Sell proceeds minus fee
        assert cash_after_sell == cash_after_buy + notional - Decimal("5.00")


# ---------------------------------------------------------------------------
# Slippage model tests
# ---------------------------------------------------------------------------


class TestSlippageModel:
    def test_no_slippage_default(self) -> None:
        broker = _make_broker()
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        order = broker.place_order("AAPL", Decimal("1"), OrderSide.BUY, OrderType.MARKET)
        assert order.filled_avg_price == Decimal("100")

    def test_fixed_bps_buy_raises_price(self) -> None:
        config = ExecutionConfig(slippage=SlippageModel(type="fixed_bps", bps=10.0))
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        order = broker.place_order("AAPL", Decimal("1"), OrderSide.BUY, OrderType.MARKET)

        # 10 bps of 100 = 0.10
        expected = Decimal("100") + Decimal("100") * Decimal("10") / Decimal("10000")
        assert order.filled_avg_price == expected

    def test_fixed_bps_sell_lowers_price(self) -> None:
        config = ExecutionConfig(slippage=SlippageModel(type="fixed_bps", bps=10.0))
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])

        # Buy first so we have a position to sell
        broker.place_order("AAPL", Decimal("1"), OrderSide.BUY, OrderType.MARKET)
        order = broker.place_order("AAPL", Decimal("1"), OrderSide.SELL, OrderType.MARKET)

        expected = Decimal("100") - Decimal("100") * Decimal("10") / Decimal("10000")
        assert order.filled_avg_price == expected

    def test_volatility_bps_scales_with_bar_range(self) -> None:
        config = ExecutionConfig(slippage=SlippageModel(type="volatility_bps", bps=100.0))
        # Use wide bar range: high=102, low=98 → range/close = 4%
        timestamps = pd.date_range("2024-01-02", periods=3, freq="B")
        df = pd.DataFrame(
            {"open": 100, "high": 102, "low": 98, "close": 100, "volume": 100000},
            index=timestamps,
        )
        broker = HistoricalBroker(
            historical_data={"AAPL": df},
            initial_cash=Decimal("100000"),
            execution_config=config,
        )
        broker.advance_to_bar(df.index[0])
        order = broker.place_order("AAPL", Decimal("1"), OrderSide.BUY, OrderType.MARKET)

        # bps_fraction = 100/10000 = 0.01; vol_ratio = (102-98)/100 = 0.04
        # effective = 0.01 * 0.04 = 0.0004 per dollar
        expected_slip = Decimal("100") * Decimal("100") / Decimal("10000") * Decimal("0.04")
        expected_price = Decimal("100") + expected_slip
        assert order.filled_avg_price == expected_price

    def test_zero_bps_no_slippage(self) -> None:
        config = ExecutionConfig(slippage=SlippageModel(type="fixed_bps", bps=0.0))
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        order = broker.place_order("AAPL", Decimal("1"), OrderSide.BUY, OrderType.MARKET)
        assert order.filled_avg_price == Decimal("100")

    def test_slippage_on_pending_limit_order(self) -> None:
        config = ExecutionConfig(slippage=SlippageModel(type="fixed_bps", bps=10.0))
        timestamps = pd.date_range("2024-01-02", periods=3, freq="B")
        df = pd.DataFrame(
            {"open": 100, "high": 105, "low": 95, "close": 100, "volume": 100000},
            index=timestamps,
        )
        broker = HistoricalBroker(
            historical_data={"AAPL": df},
            initial_cash=Decimal("100000"),
            execution_config=config,
        )
        broker.advance_to_bar(df.index[0])
        # Place a sell limit that will trigger when high >= 103
        broker.place_order("AAPL", Decimal("1"), OrderSide.BUY, OrderType.MARKET)
        order = broker.place_order(
            "AAPL",
            Decimal("1"),
            OrderSide.SELL,
            OrderType.LIMIT,
            limit_price=Decimal("103"),
        )

        broker.advance_to_bar(df.index[1])  # high=105 >= 103, triggers fill

        filled = broker.get_order(order.id)
        assert filled.status == OrderStatus.FILLED
        # Sell with slippage: fill price < limit price
        assert filled.filled_avg_price < Decimal("103")


# ---------------------------------------------------------------------------
# Fill model tests
# ---------------------------------------------------------------------------


class TestFillModel:
    def test_full_fill_default(self) -> None:
        broker = _make_broker()
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        order = broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)
        assert order.filled_qty == Decimal("10")

    def test_partial_fill_reduces_quantity(self) -> None:
        config = ExecutionConfig(fill=FillModel(type="partial", partial_pct=0.5))
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        order = broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)

        assert order.filled_qty == Decimal("5")
        assert order.status == OrderStatus.FILLED

    def test_partial_fill_minimum_one_share(self) -> None:
        config = ExecutionConfig(fill=FillModel(type="partial", partial_pct=0.01))
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        order = broker.place_order("AAPL", Decimal("1"), OrderSide.BUY, OrderType.MARKET)

        assert order.filled_qty == Decimal("1")

    def test_partial_fill_cash_accounting(self) -> None:
        config = ExecutionConfig(fill=FillModel(type="partial", partial_pct=0.5))
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        initial_cash = broker._account.cash

        broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)

        # Only 5 shares filled at $100 = $500
        assert broker._account.cash == initial_cash - Decimal("500")

    def test_partial_fill_pending_order(self) -> None:
        config = ExecutionConfig(fill=FillModel(type="partial", partial_pct=0.6))
        timestamps = pd.date_range("2024-01-02", periods=3, freq="B")
        df = pd.DataFrame(
            {"open": 100, "high": 105, "low": 95, "close": 100, "volume": 100000},
            index=timestamps,
        )
        broker = HistoricalBroker(
            historical_data={"AAPL": df},
            initial_cash=Decimal("100000"),
            execution_config=config,
        )
        broker.advance_to_bar(df.index[0])
        broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)
        stop_order = broker.place_order(
            "AAPL",
            Decimal("10"),
            OrderSide.SELL,
            OrderType.STOP,
            stop_price=Decimal("95"),
        )

        broker.advance_to_bar(df.index[1])  # low=95 triggers stop

        filled = broker.get_order(stop_order.id)
        assert filled.status == OrderStatus.FILLED
        assert filled.filled_qty == Decimal("6")  # 10 * 0.6


# ---------------------------------------------------------------------------
# Combined execution model tests
# ---------------------------------------------------------------------------


class TestCombinedExecutionConfig:
    def test_fees_and_slippage_together(self) -> None:
        config = ExecutionConfig(
            fee=FeeModel(type="fixed", value=1.0),
            slippage=SlippageModel(type="fixed_bps", bps=5.0),
        )
        broker = _make_broker(execution_config=config)
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        initial_cash = broker._account.cash

        order = broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)

        slip_per_share = Decimal("100") * Decimal("5") / Decimal("10000")
        slipped_price = Decimal("100") + slip_per_share
        notional = Decimal("10") * slipped_price
        expected_cash = initial_cash - notional - Decimal("1.00")

        assert order.filled_avg_price == slipped_price
        assert broker._account.cash == expected_cash
        assert broker.total_fees == Decimal("1.00")

    def test_backward_compat_no_execution_config(self) -> None:
        """Omitting execution_config must produce zero-cost full-fill behavior."""
        broker = _make_broker()
        broker.advance_to_bar(broker.data["AAPL"].index[0])
        initial_cash = broker._account.cash

        order = broker.place_order("AAPL", Decimal("10"), OrderSide.BUY, OrderType.MARKET)

        assert order.filled_qty == Decimal("10")
        assert order.filled_avg_price == Decimal("100")
        assert broker.total_fees == Decimal("0")
        assert broker._account.cash == initial_cash - Decimal("1000")


# ---------------------------------------------------------------------------
# Schema parity tests
# ---------------------------------------------------------------------------


class TestSchemaFields:
    def test_backtest_request_accepts_execution(self) -> None:
        req = BacktestRequest(
            strategy_type="trailing-stop",
            symbol="AAPL",
            start="2024-01-01",
            end="2024-12-31",
            trailing_pct=5.0,
            execution=ExecutionConfig(
                fee=FeeModel(type="percentage", value=0.001),
                slippage=SlippageModel(bps=5.0),
                fill=FillModel(type="full"),
            ),
        )
        assert req.execution is not None
        assert req.execution.fee.value == 0.001
        assert req.execution.slippage.bps == 5.0

    def test_backtest_request_no_execution_is_none(self) -> None:
        req = BacktestRequest(
            strategy_type="bracket",
            symbol="AAPL",
            start="2024-01-01",
            end="2024-12-31",
            take_profit=0.05,
            stop_loss=0.02,
        )
        assert req.execution is None

    def test_execution_config_defaults(self) -> None:
        config = ExecutionConfig()
        assert config.fee.type == "fixed"
        assert config.fee.value == 0.0
        assert config.slippage.bps == 0.0
        assert config.fill.type == "full"
        assert config.fill.partial_pct == 1.0

    def test_backtest_response_has_execution_fields(self) -> None:
        """BacktestResponse schema must expose execution cost fields."""
        fields = BacktestResponse.model_fields
        assert "total_fees_paid" in fields
        assert "gross_return" in fields
        assert "gross_return_pct" in fields
        assert "execution_config" in fields

    def test_invalid_fill_partial_pct(self) -> None:
        with pytest.raises(Exception):
            FillModel(type="partial", partial_pct=0.0)  # must be >= 0.01

    def test_invalid_slippage_bps(self) -> None:
        with pytest.raises(Exception):
            SlippageModel(bps=-1.0)  # must be >= 0


# ---------------------------------------------------------------------------
# Optimization schema parity
# ---------------------------------------------------------------------------


def test_optimize_request_accepts_execution() -> None:
    req = OptimizeRequest(
        strategy_type="trailing-stop",
        symbol="AAPL",
        start="2024-01-01",
        end="2024-12-31",
        params={"trailing_pct": [3.0, 5.0]},
        execution=ExecutionConfig(fee=FeeModel(type="fixed", value=1.0)),
    )
    assert req.execution is not None
    assert req.execution.fee.value == 1.0
