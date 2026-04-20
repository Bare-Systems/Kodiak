"""Database schema migrations for the kodiak schema.

Run once on first deployment or after pulling schema changes:
    from kodiak.db.migrations import ensure_schema
    ensure_schema()

Or via CLI:
    kodiak db migrate

Idempotent — safe to re-run; uses CREATE TABLE IF NOT EXISTS throughout.
"""

from __future__ import annotations

_DDL = """
-- ============================================================
-- Kodiak schema
-- ============================================================
CREATE SCHEMA IF NOT EXISTS kodiak;

-- ============================================================
-- strategies — mutable strategy state (replaces strategies.yaml)
-- ============================================================
CREATE TABLE IF NOT EXISTS kodiak.strategies (
    id                      TEXT        PRIMARY KEY,
    symbol                  TEXT        NOT NULL,
    strategy_type           TEXT        NOT NULL,
    phase                   TEXT        NOT NULL DEFAULT 'pending',
    quantity                INTEGER     NOT NULL,
    enabled                 BOOLEAN     NOT NULL DEFAULT TRUE,

    -- Entry configuration
    entry_type              TEXT        NOT NULL DEFAULT 'market',
    entry_price             TEXT,
    entry_condition         TEXT,

    -- Exit configuration — trailing stop
    trailing_stop_pct       TEXT,

    -- Exit configuration — pullback-trailing
    pullback_pct            TEXT,
    pullback_reference_price TEXT,

    -- Exit configuration — bracket
    take_profit_pct         TEXT,
    stop_loss_pct           TEXT,

    -- Exit configuration — scale-out / grid (structured JSON)
    scale_targets           JSONB,
    grid_config             JSONB,

    -- State tracking
    entry_order_id          TEXT,
    entry_fill_price        TEXT,
    high_watermark          TEXT,
    exit_order_ids          JSONB       NOT NULL DEFAULT '[]'::jsonb,
    scale_state             JSONB,
    grid_state              JSONB,

    -- Scheduling
    schedule_at             TIMESTAMPTZ,
    schedule_enabled        BOOLEAN     NOT NULL DEFAULT FALSE,

    -- Metadata
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes                   TEXT
);

-- ============================================================
-- orders — local OMS order cache (replaces orders.yaml)
-- ============================================================
CREATE TABLE IF NOT EXISTS kodiak.orders (
    id          TEXT        PRIMARY KEY,
    symbol      TEXT        NOT NULL,
    side        TEXT        NOT NULL,
    qty         TEXT        NOT NULL,
    order_type  TEXT        NOT NULL,
    limit_price TEXT,
    external_id TEXT,
    status      TEXT        NOT NULL DEFAULT 'new',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_external_id
    ON kodiak.orders (external_id)
    WHERE external_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON kodiak.orders (status);
"""


def ensure_schema() -> None:
    """Create the kodiak schema and tables if they don't exist.

    Safe to call multiple times — all statements are idempotent.

    Raises:
        RuntimeError: If KODIAK_DATABASE_URL is not configured.
        psycopg2.Error: On DDL failure.
    """
    from kodiak.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_DDL)


def get_ddl() -> str:
    """Return the raw DDL string for inspection or manual application."""
    return _DDL
