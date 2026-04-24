"""Order placement and management service functions."""

from __future__ import annotations

from decimal import Decimal

from kodiak.api.broker import OrderSide, OrderStatus, OrderType
from kodiak.app import get_broker
from kodiak.audit import log_action as audit_log
from kodiak.core.safety import SafetyCheck
from kodiak.data.ledger import TradeLedger
from kodiak.errors import BrokerError, SafetyError
from kodiak.oms.store import save_order
from kodiak.schemas.orders import OrderRequest, OrderResponse
from kodiak.utils.config import Config
from kodiak.utils.logging import get_logger

logger = get_logger("trader.app.orders")


def place_order(config: Config, request: OrderRequest) -> OrderResponse:
    """Place a limit order.

    Args:
        config: Application configuration.
        request: Order request schema.

    Returns:
        Order response schema.

    Raises:
        SafetyError: If order blocked by safety checks.
        BrokerError: If broker call fails.
    """
    logger = get_logger("trader.trades")
    broker = get_broker(config)
    symbol = request.symbol.upper()
    is_buy = request.side.lower() == "buy"

    # Safety checks
    ledger = TradeLedger()
    checker = SafetyCheck(broker, ledger)
    check_price = Decimal(str(request.price))

    allowed, reason = checker.check_order(symbol, request.qty, check_price, is_buy=is_buy)
    if not allowed:
        audit_log(
            "place_order_blocked",
            {"symbol": symbol, "qty": request.qty, "side": request.side, "reason": reason},
            error=reason,
            log_dir=config.log_dir,
        )
        raise SafetyError(
            message=f"Order blocked by safety checks: {reason}",
            code="ORDER_BLOCKED",
            details={"reason": reason, "symbol": symbol},
        )

    # Place order
    side = OrderSide.BUY if is_buy else OrderSide.SELL
    try:
        order = broker.place_order(
            symbol=symbol,
            qty=Decimal(str(request.qty)),
            side=side,
            order_type=OrderType.LIMIT,
            limit_price=Decimal(str(request.price)),
        )
    except Exception as e:
        audit_log(
            "place_order",
            {"symbol": symbol, "qty": request.qty, "side": request.side},
            error=str(e),
            log_dir=config.log_dir,
        )
        raise BrokerError(
            message=f"Failed to place order: {e}",
            code="ORDER_PLACEMENT_FAILED",
        )

    # Persist locally (non-blocking)
    try:
        save_order(order)
    except Exception:
        logger.exception("Failed to persist order locally")

    logger.info(
        f"{request.side.upper()} {request.qty} {symbol} | "
        f"Order ID: {order.id} | Status: {order.status.value}"
    )
    audit_log(
        "place_order",
        {"symbol": symbol, "qty": request.qty, "side": request.side, "order_id": order.id},
        log_dir=config.log_dir,
    )
    return OrderResponse.from_domain(order)


def list_orders(config: Config, show_all: bool = False) -> list[OrderResponse]:
    """List orders from broker.

    Args:
        config: Application configuration.
        show_all: If True, show all orders. Otherwise only open/pending.

    Returns:
        List of order response schemas.
    """
    broker = get_broker(config)
    try:
        orders_list = broker.get_orders()
    except Exception as e:
        if "ConfigurationError" in type(e).__name__:
            raise
        raise BrokerError(
            message=f"Failed to list orders: {e}",
            code="BROKER_FETCH_FAILED",
        )

    if not show_all:
        open_statuses = {
            OrderStatus.NEW,
            OrderStatus.PENDING,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
        }
        orders_list = [o for o in orders_list if o.status in open_statuses]

    return [OrderResponse.from_domain(o) for o in orders_list]


def cancel_order(config: Config, order_id: str) -> dict[str, str]:
    """Cancel an open order.

    Args:
        config: Application configuration.
        order_id: Order ID to cancel.

    Returns:
        Dict with status message.

    Raises:
        BrokerError: If cancellation fails.
    """
    broker = get_broker(config)
    success = broker.cancel_order(order_id)

    if success:
        # Update local order status to canceled
        try:
            canceled_order = broker.get_order(order_id)
            if canceled_order:
                save_order(canceled_order)
        except Exception:
            logger.debug(f"Failed to update local order {order_id} after cancellation")

        audit_log("cancel_order", {"order_id": order_id}, log_dir=config.log_dir)
        return {"status": "canceled", "order_id": order_id}
    else:
        audit_log(
            "cancel_order",
            {"order_id": order_id},
            error="Cancel failed",
            log_dir=config.log_dir,
        )
        raise BrokerError(
            message=f"Failed to cancel order {order_id}",
            code="CANCEL_FAILED",
            details={"order_id": order_id},
        )
