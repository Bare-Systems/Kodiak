"""Strategies REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
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
from kodiak.errors import AppError

router = APIRouter(prefix="/strategies")


@router.get("/")
def get_strategies():
    """List all strategies."""
    try:
        return list_strategies()
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str):
    """Get strategy details."""
    try:
        return get_strategy_detail(strategy_id)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


class CreateStrategyRequest(BaseModel):
    strategy_type: str
    symbol: str
    qty: int
    trailing_stop_pct: float | None = None
    take_profit_pct: float | None = None
    stop_loss_pct: float | None = None


@router.post("/")
def create(req: CreateStrategyRequest):
    """Create a new strategy."""
    try:
        return create_strategy(**req.model_dump(exclude_none=True))
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.delete("/{strategy_id}")
def delete_strategy(strategy_id: str):
    """Remove a strategy."""
    try:
        return remove_strategy(strategy_id)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/{strategy_id}/pause")
def pause(strategy_id: str):
    """Pause a strategy."""
    try:
        return pause_strategy(strategy_id)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.post("/{strategy_id}/resume")
def resume(strategy_id: str):
    """Resume a strategy."""
    try:
        return resume_strategy(strategy_id)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


class EnableRequest(BaseModel):
    enabled: bool


@router.post("/{strategy_id}/enabled")
def set_enabled(strategy_id: str, req: EnableRequest):
    """Enable or disable a strategy."""
    try:
        return set_strategy_enabled(strategy_id, req.enabled)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
