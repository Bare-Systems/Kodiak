"""FastAPI REST application for Kodiak Server.

All routes delegate to kodiak.app.* service functions and return
the same Pydantic schemas used by the MCP tools.
"""

from __future__ import annotations

from fastapi import FastAPI

from kodiak_server.rest.routes import engine, orders, portfolio, strategies


def create_rest_app() -> FastAPI:
    """Create and configure the REST API application."""
    app = FastAPI(
        title="Kodiak REST API",
        version="2.0.0",
    )

    app.include_router(engine.router, tags=["engine"])
    app.include_router(portfolio.router, tags=["portfolio"])
    app.include_router(orders.router, tags=["orders"])
    app.include_router(strategies.router, tags=["strategies"])

    return app
