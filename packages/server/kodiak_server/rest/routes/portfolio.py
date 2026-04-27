"""Portfolio REST API routes."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from kodiak.app.portfolio import (
    calculate_position_size_app,
    get_balance,
    get_portfolio_analytics,
    get_portfolio_summary,
    get_positions,
    get_quote,
    get_rebalance_plan_app,
    get_top_movers,
)
from kodiak.schemas.portfolio import PositionSizingRequest, RebalanceRequest
from kodiak.utils.config import load_config

from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/portfolio")


@router.get("/balance")
def balance(ctx: RequestContext = Depends(get_request_context)) -> dict[str, Any]:
    """Get account balance."""
    config = load_config()
    return ok(get_balance(config), ctx.request_id)


@router.get("/positions")
def positions(ctx: RequestContext = Depends(get_request_context)) -> dict[str, Any]:
    """Get open positions."""
    config = load_config()
    return ok(get_positions(config), ctx.request_id)


@router.get("/summary")
def summary(ctx: RequestContext = Depends(get_request_context)) -> dict[str, Any]:
    """Get full portfolio summary."""
    config = load_config()
    return ok(get_portfolio_summary(config), ctx.request_id)


@router.get("/analytics")
def analytics(
    lookback_days: int = Query(252, ge=1),
    benchmark_symbol: str = Query("SPY"),
    end_date: date | None = Query(None),
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Get portfolio analytics with transaction-level reconstruction when available."""
    config = load_config()
    return ok(
        get_portfolio_analytics(
            config,
            lookback_days=lookback_days,
            benchmark_symbol=benchmark_symbol,
            end_date=end_date,
        ),
        ctx.request_id,
    )


@router.post("/position-size")
def position_size(
    request: PositionSizingRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Calculate a target size for a symbol."""
    config = load_config()
    return ok(calculate_position_size_app(config, request), ctx.request_id)


@router.post("/rebalance-plan")
def rebalance_plan(
    request: RebalanceRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Generate a dry-run rebalance plan."""
    config = load_config()
    return ok(get_rebalance_plan_app(config, request), ctx.request_id)


@router.get("/quote/{symbol}")
def quote(symbol: str, ctx: RequestContext = Depends(get_request_context)) -> dict[str, Any]:
    """Get a quote for a symbol."""
    config = load_config()
    return ok(get_quote(config, symbol), ctx.request_id)


@router.get("/movers")
def movers(
    market_type: str = Query("stocks"),
    limit: int = Query(10),
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Get top movers."""
    config = load_config()
    return ok(get_top_movers(config, market_type=market_type, limit=limit), ctx.request_id)
