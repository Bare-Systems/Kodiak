"""PostgreSQL-backed order store.

Implements the same function signatures as kodiak.oms.store so the OMS can
route transparently. All functions read/write the kodiak.orders table via
KODIAK_DATABASE_URL.

The local order cache is a convenience layer — the authoritative source for
order state is always the broker. This table mirrors what has been submitted
so Kodiak can do local lookups without hitting the broker API on every cycle.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg2.extras

from kodiak.models.order import Order, OrderSide, OrderStatus, OrderType


def _order_to_row(order: Order) -> dict[str, Any]:
    """Serialise an Order to a dict for INSERT/UPDATE."""
    from decimal import Decimal

    return {
        "id": order.id,
        "symbol": order.symbol,
        "side": order.side.value,
        "qty": str(order.qty),
        "order_type": order.order_type.value,
        "limit_price": str(order.limit_price) if order.limit_price is not None else None,
        "external_id": order.external_id,
        "status": order.status.value,
    }


def _row_to_order(row: psycopg2.extras.DictRow) -> Order:
    """Deserialise a psycopg2 DictRow back to an Order."""
    return Order.from_dict(dict(row))


_UPSERT_SQL = """
INSERT INTO kodiak.orders (id, symbol, side, qty, order_type, limit_price, external_id, status)
VALUES (%(id)s, %(symbol)s, %(side)s, %(qty)s, %(order_type)s, %(limit_price)s, %(external_id)s, %(status)s)
ON CONFLICT (id) DO UPDATE SET
    symbol      = EXCLUDED.symbol,
    side        = EXCLUDED.side,
    qty         = EXCLUDED.qty,
    order_type  = EXCLUDED.order_type,
    limit_price = EXCLUDED.limit_price,
    external_id = EXCLUDED.external_id,
    status      = EXCLUDED.status,
    updated_at  = NOW()
"""

_UPSERT_BY_EXTERNAL_SQL = """
INSERT INTO kodiak.orders (id, symbol, side, qty, order_type, limit_price, external_id, status)
VALUES (%(id)s, %(symbol)s, %(side)s, %(qty)s, %(order_type)s, %(limit_price)s, %(external_id)s, %(status)s)
ON CONFLICT (id) DO UPDATE SET
    status      = EXCLUDED.status,
    external_id = EXCLUDED.external_id,
    updated_at  = NOW()
"""


def load_orders() -> list[Order]:
    """Load all orders from the database, newest first."""
    from kodiak.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM kodiak.orders ORDER BY created_at DESC")
            rows = cur.fetchall()
    return [_row_to_order(r) for r in rows]


def save_order(order_obj: object) -> None:
    """Insert or update a single order.

    Accepts a local Order instance or any broker-like order object.
    Matches on `id` first; if a row with the same `external_id` exists,
    updates its status instead (handles broker-id → local-id mapping).
    """
    from kodiak.db.connection import get_connection
    from kodiak.oms.store import _to_local_order

    local = order_obj if isinstance(order_obj, Order) else _to_local_order(order_obj)
    row = _order_to_row(local)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_UPSERT_SQL, row)


def save_orders(orders: list[Order]) -> None:
    """Batch upsert a list of orders."""
    for o in orders:
        save_order(o)
