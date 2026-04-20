"""PostgreSQL connection management.

Usage:
    from kodiak.db.connection import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")

The connection is auto-committed on clean exit and rolled back on exception.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.extras


def get_db_url() -> str | None:
    """Return KODIAK_DATABASE_URL if set, else None."""
    return os.getenv("KODIAK_DATABASE_URL") or None


def db_available() -> bool:
    """True when a database URL is configured."""
    return get_db_url() is not None


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Yield a psycopg2 connection that auto-commits or rolls back.

    JSONB columns are automatically handled: Python dicts/lists can be
    assigned directly to JSONB parameters — psycopg2 serialises them.

    Raises:
        RuntimeError: If KODIAK_DATABASE_URL is not configured.
        psycopg2.Error: On connection or query failure.
    """
    url = get_db_url()
    if url is None:
        raise RuntimeError(
            "KODIAK_DATABASE_URL environment variable is not set. "
            "Set it to a libpq connection string to use the PostgreSQL store, "
            "e.g. postgresql://user:pass@host:5432/dbname"
        )

    # Register native JSON/JSONB <-> Python dict/list adaptation globally
    # so we can pass dicts directly to JSONB parameters.
    psycopg2.extras.register_default_jsonb(globally=True)

    conn = psycopg2.connect(url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
