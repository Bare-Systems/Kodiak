"""PostgreSQL-backed strategy store.

Implements the same function signatures as kodiak.strategies.loader so the
loader can route transparently. All functions read/write the kodiak.strategies
table via KODIAK_DATABASE_URL.

Strategy → DB mapping uses Strategy.to_dict() for serialisation and
Strategy.from_dict() for deserialisation — the same path used by YAML.
The only difference: JSONB columns (scale_targets, grid_config, etc.) are
passed as Python dicts/lists; psycopg2 handles JSON serialisation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg2.extras

from kodiak.strategies.models import Strategy


def _dict_to_row(d: dict[str, Any]) -> dict[str, Any]:
    """Prepare a Strategy.to_dict() payload for INSERT/UPDATE.

    - Converts ISO datetime strings back to datetime objects for TIMESTAMPTZ.
    - JSONB fields are kept as Python dicts/lists (psycopg2 serialises them).
    """
    row: dict[str, Any] = dict(d)

    # TIMESTAMPTZ — parse ISO strings back to datetime
    for ts_field in ("created_at", "updated_at", "schedule_at"):
        val = row.get(ts_field)
        if isinstance(val, str):
            row[ts_field] = datetime.fromisoformat(val)
        # None stays None

    return row


def _row_to_dict(row: psycopg2.extras.DictRow) -> dict[str, Any]:
    """Convert a psycopg2 DictRow to a plain dict compatible with Strategy.from_dict()."""
    d = dict(row)
    # TIMESTAMPTZ columns come back as datetime objects; Strategy.from_dict
    # accepts either ISO strings or datetime objects via fromisoformat.
    # Convert to ISO string to reuse the existing parsing path uniformly.
    for ts_field in ("created_at", "updated_at", "schedule_at"):
        val = d.get(ts_field)
        if isinstance(val, datetime):
            d[ts_field] = val.isoformat()
        # None stays None
    return d


_INSERT_SQL = """
INSERT INTO kodiak.strategies (
    id, symbol, strategy_type, phase, quantity, enabled,
    entry_type, entry_price, entry_condition,
    trailing_stop_pct, pullback_pct, pullback_reference_price,
    take_profit_pct, stop_loss_pct,
    scale_targets, grid_config,
    entry_order_id, entry_fill_price, high_watermark,
    exit_order_ids, scale_state, grid_state,
    schedule_at, schedule_enabled,
    created_at, updated_at, notes
) VALUES (
    %(id)s, %(symbol)s, %(strategy_type)s, %(phase)s, %(quantity)s, %(enabled)s,
    %(entry_type)s, %(entry_price)s, %(entry_condition)s,
    %(trailing_stop_pct)s, %(pullback_pct)s, %(pullback_reference_price)s,
    %(take_profit_pct)s, %(stop_loss_pct)s,
    %(scale_targets)s, %(grid_config)s,
    %(entry_order_id)s, %(entry_fill_price)s, %(high_watermark)s,
    %(exit_order_ids)s, %(scale_state)s, %(grid_state)s,
    %(schedule_at)s, %(schedule_enabled)s,
    %(created_at)s, %(updated_at)s, %(notes)s
)
ON CONFLICT (id) DO UPDATE SET
    symbol                  = EXCLUDED.symbol,
    strategy_type           = EXCLUDED.strategy_type,
    phase                   = EXCLUDED.phase,
    quantity                = EXCLUDED.quantity,
    enabled                 = EXCLUDED.enabled,
    entry_type              = EXCLUDED.entry_type,
    entry_price             = EXCLUDED.entry_price,
    entry_condition         = EXCLUDED.entry_condition,
    trailing_stop_pct       = EXCLUDED.trailing_stop_pct,
    pullback_pct            = EXCLUDED.pullback_pct,
    pullback_reference_price = EXCLUDED.pullback_reference_price,
    take_profit_pct         = EXCLUDED.take_profit_pct,
    stop_loss_pct           = EXCLUDED.stop_loss_pct,
    scale_targets           = EXCLUDED.scale_targets,
    grid_config             = EXCLUDED.grid_config,
    entry_order_id          = EXCLUDED.entry_order_id,
    entry_fill_price        = EXCLUDED.entry_fill_price,
    high_watermark          = EXCLUDED.high_watermark,
    exit_order_ids          = EXCLUDED.exit_order_ids,
    scale_state             = EXCLUDED.scale_state,
    grid_state              = EXCLUDED.grid_state,
    schedule_at             = EXCLUDED.schedule_at,
    schedule_enabled        = EXCLUDED.schedule_enabled,
    updated_at              = EXCLUDED.updated_at,
    notes                   = EXCLUDED.notes
"""


def load_strategies() -> list[Strategy]:
    """Load all strategies from the database."""
    from kodiak.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM kodiak.strategies ORDER BY created_at")
            rows = cur.fetchall()
    return [Strategy.from_dict(_row_to_dict(r)) for r in rows]


def save_strategy(strategy: Strategy) -> None:
    """Insert or update a single strategy (upsert by id)."""
    strategy.updated_at = datetime.now()
    row = _dict_to_row(strategy.to_dict())

    from kodiak.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_INSERT_SQL, row)


def save_strategies(strategies: list[Strategy]) -> None:
    """Batch upsert a list of strategies."""
    for s in strategies:
        save_strategy(s)


def delete_strategy(strategy_id: str) -> bool:
    """Delete a strategy by ID. Returns True if a row was removed."""
    from kodiak.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kodiak.strategies WHERE id = %s",
                (strategy_id,),
            )
            return (cur.rowcount or 0) > 0


def get_strategy(strategy_id: str) -> Strategy | None:
    """Fetch a single strategy by ID, or None if not found."""
    from kodiak.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(
                "SELECT * FROM kodiak.strategies WHERE id = %s",
                (strategy_id,),
            )
            row = cur.fetchone()
    if row is None:
        return None
    return Strategy.from_dict(_row_to_dict(row))


def enable_strategy(strategy_id: str, enabled: bool = True) -> bool:
    """Enable or disable a strategy. Returns True if found and updated."""
    from kodiak.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE kodiak.strategies SET enabled = %s, updated_at = NOW() WHERE id = %s",
                (enabled, strategy_id),
            )
            return (cur.rowcount or 0) > 0


def get_active_strategies() -> list[Strategy]:
    """Return all enabled, non-terminal, schedule-ready strategies."""
    now = datetime.now()
    strategies = load_strategies()
    active = []
    for s in strategies:
        if not s.enabled:
            continue
        if s.schedule_enabled and s.schedule_at and s.schedule_at > now:
            continue
        if not s.is_active():
            continue
        active.append(s)
    return active
