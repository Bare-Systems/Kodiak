"""Kodiak PostgreSQL persistence layer.

All mutable state (strategies, orders) is stored in the `kodiak` schema
of the Postgres instance pointed at by KODIAK_DATABASE_URL.

Set KODIAK_DATABASE_URL to a libpq-compatible connection string, e.g.:
    postgresql://user:password@host:5432/dbname

If KODIAK_DATABASE_URL is not set, the strategy and order stores fall
back to the legacy YAML files so local development and CI work without
a running database.
"""
