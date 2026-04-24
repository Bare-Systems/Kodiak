"""Portfolio sizing and rebalancing utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_DOWN, Decimal

from kodiak.api.broker import Account, Position


@dataclass
class PositionSizingResult:
    """Recommended position size for a single symbol."""

    generated_at: datetime
    symbol: str
    method: str
    reference_price: Decimal
    current_qty: Decimal
    target_qty: Decimal
    delta_qty: Decimal
    current_position_value: Decimal
    target_position_value: Decimal
    estimated_order_value: Decimal
    estimated_weight_pct: Decimal
    target_weight_pct: Decimal | None
    target_value: Decimal | None
    risk_budget: Decimal | None
    stop_loss_pct: Decimal | None
    capped_by: list[str]


@dataclass
class RebalanceTrade:
    """A single dry-run rebalance trade."""

    symbol: str
    side: str
    qty: Decimal
    reference_price: Decimal
    estimated_value: Decimal
    current_qty: Decimal
    target_qty: Decimal
    current_weight_pct: Decimal
    target_weight_pct: Decimal
    drift_pct: Decimal


@dataclass
class RebalancePlan:
    """Dry-run rebalance plan."""

    generated_at: datetime
    total_equity: Decimal
    current_cash: Decimal
    projected_cash: Decimal
    current_cash_weight_pct: Decimal
    projected_cash_weight_pct: Decimal
    drift_threshold_pct: Decimal
    cash_buffer_pct: Decimal
    liquidate_unmentioned: bool
    rebalance_required: bool
    trade_count: int
    estimated_turnover_pct: Decimal
    estimated_net_cash_change: Decimal
    target_weights: dict[str, Decimal]
    trades: list[RebalanceTrade]


def calculate_position_size(
    *,
    symbol: str,
    method: str,
    reference_price: Decimal,
    account: Account,
    current_qty: Decimal = Decimal("0"),
    target_value: Decimal | None = None,
    target_weight_pct: Decimal | None = None,
    risk_budget: Decimal | None = None,
    stop_loss_pct: Decimal | None = None,
    available_capital: Decimal | None = None,
    max_position_value: Decimal | None = None,
    max_position_weight_pct: Decimal | None = None,
    lot_size: int = 1,
    generated_at: datetime | None = None,
) -> PositionSizingResult:
    """Calculate a recommended target position size."""
    generated_at = generated_at or datetime.now()
    if reference_price <= 0:
        raise ValueError("reference_price must be greater than 0")
    if lot_size < 1:
        raise ValueError("lot_size must be at least 1")
    if account.equity <= 0:
        raise ValueError("account equity must be greater than 0")

    method = method.lower().replace("-", "_")
    if method not in {"target_value", "target_weight", "risk_budget"}:
        raise ValueError("method must be one of: target_value, target_weight, risk_budget")

    available_capital = available_capital if available_capital is not None else account.buying_power
    if available_capital < 0:
        raise ValueError("available_capital cannot be negative")

    current_position_value = current_qty * reference_price
    capped_by: list[str] = []

    desired_position_value: Decimal
    if method == "target_value":
        if target_value is None or target_value <= 0:
            raise ValueError("target_value is required and must be greater than 0 for target_value sizing")
        desired_position_value = target_value
    elif method == "target_weight":
        if target_weight_pct is None or target_weight_pct <= 0:
            raise ValueError(
                "target_weight_pct is required and must be greater than 0 for target_weight sizing"
            )
        desired_position_value = account.equity * (target_weight_pct / Decimal("100"))
    else:
        if risk_budget is None or risk_budget <= 0:
            raise ValueError("risk_budget is required and must be greater than 0 for risk_budget sizing")
        if stop_loss_pct is None or stop_loss_pct <= 0:
            raise ValueError(
                "stop_loss_pct is required and must be greater than 0 for risk_budget sizing"
            )
        per_share_risk = reference_price * (stop_loss_pct / Decimal("100"))
        if per_share_risk <= 0:
            raise ValueError("risk_budget sizing requires a positive per-share risk")
        raw_target_qty = risk_budget / per_share_risk
        desired_position_value = raw_target_qty * reference_price

    if max_position_value is not None and max_position_value >= 0 and desired_position_value > max_position_value:
        desired_position_value = max_position_value
        capped_by.append("max_position_value")

    if max_position_weight_pct is not None:
        if max_position_weight_pct < 0 or max_position_weight_pct > 100:
            raise ValueError("max_position_weight_pct must be between 0 and 100")
        max_weight_value = account.equity * (max_position_weight_pct / Decimal("100"))
        if desired_position_value > max_weight_value:
            desired_position_value = max_weight_value
            capped_by.append("max_position_weight_pct")

    affordable_position_value = current_position_value + available_capital
    if desired_position_value > affordable_position_value:
        desired_position_value = affordable_position_value
        capped_by.append("available_capital")

    target_qty_result = _round_down_to_lot(desired_position_value / reference_price, lot_size)
    target_position_value = target_qty_result * reference_price
    delta_qty = target_qty_result - current_qty
    estimated_order_value = abs(delta_qty) * reference_price
    estimated_weight_pct = (
        (target_position_value / account.equity) * Decimal("100") if account.equity else Decimal("0")
    )

    implied_target_weight = (
        (target_position_value / account.equity) * Decimal("100") if account.equity else None
    )

    return PositionSizingResult(
        generated_at=generated_at,
        symbol=symbol.upper(),
        method=method,
        reference_price=reference_price,
        current_qty=current_qty,
        target_qty=target_qty_result,
        delta_qty=delta_qty,
        current_position_value=current_position_value,
        target_position_value=target_position_value,
        estimated_order_value=estimated_order_value,
        estimated_weight_pct=estimated_weight_pct,
        target_weight_pct=target_weight_pct if method == "target_weight" else implied_target_weight,
        target_value=target_value if method == "target_value" else target_position_value,
        risk_budget=risk_budget,
        stop_loss_pct=stop_loss_pct,
        capped_by=capped_by,
    )


def generate_rebalance_plan(
    *,
    account: Account,
    current_positions: list[Position],
    target_weights: dict[str, Decimal],
    reference_prices: dict[str, Decimal],
    drift_threshold_pct: Decimal = Decimal("1"),
    cash_buffer_pct: Decimal = Decimal("0"),
    liquidate_unmentioned: bool = False,
    lot_size: int = 1,
    max_position_weight_pct: Decimal | None = None,
    generated_at: datetime | None = None,
) -> RebalancePlan:
    """Generate a dry-run rebalance plan."""
    generated_at = generated_at or datetime.now()
    if account.equity <= 0:
        raise ValueError("account equity must be greater than 0")
    if drift_threshold_pct < 0:
        raise ValueError("drift_threshold_pct cannot be negative")
    if cash_buffer_pct < 0 or cash_buffer_pct > 100:
        raise ValueError("cash_buffer_pct must be between 0 and 100")
    if lot_size < 1:
        raise ValueError("lot_size must be at least 1")

    normalized_targets = {symbol.upper(): weight for symbol, weight in target_weights.items()}
    for symbol, weight in normalized_targets.items():
        if weight < 0:
            raise ValueError(f"target weight for {symbol} cannot be negative")
        if weight > 100:
            raise ValueError(f"target weight for {symbol} cannot exceed 100")
        if max_position_weight_pct is not None and weight > max_position_weight_pct:
            raise ValueError(
                f"target weight for {symbol} exceeds max_position_weight_pct ({max_position_weight_pct})"
            )

    if sum(normalized_targets.values(), Decimal("0")) > Decimal("100"):
        raise ValueError("sum of target weights cannot exceed 100")

    current_map = {position.symbol.upper(): position for position in current_positions}
    symbols = set(current_map) | set(normalized_targets)

    trades: list[RebalanceTrade] = []
    total_buy_value = Decimal("0")
    total_sell_value = Decimal("0")

    for symbol in sorted(symbols):
        current_position = current_map.get(symbol)
        current_qty = current_position.qty if current_position else Decimal("0")

        if current_position:
            reference_price = current_position.current_price
            current_value = current_position.market_value
        else:
            if symbol not in reference_prices:
                raise ValueError(f"reference price missing for {symbol}")
            reference_price = reference_prices[symbol]
            current_value = Decimal("0")

        if reference_price <= 0:
            raise ValueError(f"reference price for {symbol} must be greater than 0")

        current_weight_pct = (
            (current_value / account.equity) * Decimal("100") if account.equity else Decimal("0")
        )
        if symbol in normalized_targets:
            target_weight_pct = normalized_targets[symbol]
        elif liquidate_unmentioned:
            target_weight_pct = Decimal("0")
        else:
            target_weight_pct = current_weight_pct

        target_value = account.equity * (target_weight_pct / Decimal("100"))
        target_qty = _round_down_to_lot(target_value / reference_price, lot_size)
        drift_pct = target_weight_pct - current_weight_pct
        delta_qty = target_qty - current_qty

        should_trade = delta_qty != 0 and (
            abs(drift_pct) >= drift_threshold_pct
            or target_weight_pct == 0
            or symbol in normalized_targets and current_qty == 0
        )

        if should_trade:
            side = "buy" if delta_qty > 0 else "sell"
            estimated_value = abs(delta_qty) * reference_price
            if side == "buy":
                total_buy_value += estimated_value
            else:
                total_sell_value += estimated_value

            trades.append(
                RebalanceTrade(
                    symbol=symbol,
                    side=side,
                    qty=abs(delta_qty),
                    reference_price=reference_price,
                    estimated_value=estimated_value,
                    current_qty=current_qty,
                    target_qty=target_qty,
                    current_weight_pct=current_weight_pct,
                    target_weight_pct=target_weight_pct,
                    drift_pct=drift_pct,
                )
            )

    projected_cash = account.cash + total_sell_value - total_buy_value
    minimum_cash = account.equity * (cash_buffer_pct / Decimal("100"))
    if projected_cash < minimum_cash:
        raise ValueError(
            "rebalance plan would violate the requested cash buffer; reduce targets or liquidate more positions"
        )

    estimated_turnover_pct = (
        ((total_buy_value + total_sell_value) / account.equity) * Decimal("100")
        if account.equity
        else Decimal("0")
    )
    current_cash_weight_pct = (
        (account.cash / account.equity) * Decimal("100") if account.equity else Decimal("0")
    )
    projected_cash_weight_pct = (
        (projected_cash / account.equity) * Decimal("100") if account.equity else Decimal("0")
    )

    return RebalancePlan(
        generated_at=generated_at,
        total_equity=account.equity,
        current_cash=account.cash,
        projected_cash=projected_cash,
        current_cash_weight_pct=current_cash_weight_pct,
        projected_cash_weight_pct=projected_cash_weight_pct,
        drift_threshold_pct=drift_threshold_pct,
        cash_buffer_pct=cash_buffer_pct,
        liquidate_unmentioned=liquidate_unmentioned,
        rebalance_required=bool(trades),
        trade_count=len(trades),
        estimated_turnover_pct=estimated_turnover_pct,
        estimated_net_cash_change=projected_cash - account.cash,
        target_weights=normalized_targets,
        trades=sorted(
            trades,
            key=lambda trade: (trade.side != "sell", -trade.estimated_value, trade.symbol),
        ),
    )


def _round_down_to_lot(quantity: Decimal, lot_size: int) -> Decimal:
    """Round a quantity down to the nearest supported lot size."""
    if quantity <= 0:
        return Decimal("0")
    lot = Decimal(str(lot_size))
    lots = (quantity / lot).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return lots * lot
