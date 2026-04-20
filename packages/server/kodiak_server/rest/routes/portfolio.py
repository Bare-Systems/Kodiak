"""Portfolio REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from kodiak.app.portfolio import (
    get_balance,
    get_portfolio_summary,
    get_positions,
    get_quote,
    get_top_movers,
)
from kodiak.utils.config import load_config
from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/portfolio")


@router.get("/balance")
def balance(ctx: RequestContext = Depends(get_request_context)):
    """Get account balance."""
    config = load_config()
    return ok(get_balance(config), ctx.request_id)


@router.get("/positions")
def positions(ctx: RequestContext = Depends(get_request_context)):
    """Get open positions."""
    config = load_config()
    return ok(get_positions(config), ctx.request_id)


@router.get("/summary")
def summary(ctx: RequestContext = Depends(get_request_context)):
    """Get full portfolio summary."""
    config = load_config()
    return ok(get_portfolio_summary(config), ctx.request_id)


@router.get("/quote/{symbol}")
def quote(symbol: str, ctx: RequestContext = Depends(get_request_context)):
    """Get a quote for a symbol."""
    config = load_config()
    return ok(get_quote(config, symbol), ctx.request_id)


@router.get("/movers")
def movers(
    market_type: str = Query("stocks"),
    limit: int = Query(10),
    ctx: RequestContext = Depends(get_request_context),
):
    """Get top movers."""
    config = load_config()
    return ok(get_top_movers(config, market_type=market_type, limit=limit), ctx.request_id)
