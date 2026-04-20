"""Strategies REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from kodiak.app.strategies import (
    create_strategy,
    get_strategy_detail,
    list_strategies,
    pause_strategy,
    remove_strategy,
    resume_strategy,
    set_strategy_enabled,
)
from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/strategies")


@router.get("/")
def get_strategies(ctx: RequestContext = Depends(get_request_context)):
    """List all strategies."""
    return ok(list_strategies(), ctx.request_id)


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str, ctx: RequestContext = Depends(get_request_context)):
    """Get strategy details."""
    return ok(get_strategy_detail(strategy_id), ctx.request_id)


class CreateStrategyRequest(BaseModel):
    strategy_type: str
    symbol: str
    qty: int
    trailing_stop_pct: float | None = None
    take_profit_pct: float | None = None
    stop_loss_pct: float | None = None


@router.post("/")
def create(
    req: CreateStrategyRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """Create a new strategy."""
    return ok(create_strategy(**req.model_dump(exclude_none=True)), ctx.request_id)


@router.delete("/{strategy_id}")
def delete_strategy(strategy_id: str, ctx: RequestContext = Depends(get_request_context)):
    """Remove a strategy."""
    return ok(remove_strategy(strategy_id), ctx.request_id)


@router.post("/{strategy_id}/pause")
def pause(strategy_id: str, ctx: RequestContext = Depends(get_request_context)):
    """Pause a strategy."""
    return ok(pause_strategy(strategy_id), ctx.request_id)


@router.post("/{strategy_id}/resume")
def resume(strategy_id: str, ctx: RequestContext = Depends(get_request_context)):
    """Resume a strategy."""
    return ok(resume_strategy(strategy_id), ctx.request_id)


class EnableRequest(BaseModel):
    enabled: bool


@router.post("/{strategy_id}/enabled")
def set_enabled(
    strategy_id: str,
    req: EnableRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """Enable or disable a strategy."""
    return ok(set_strategy_enabled(strategy_id, req.enabled), ctx.request_id)
