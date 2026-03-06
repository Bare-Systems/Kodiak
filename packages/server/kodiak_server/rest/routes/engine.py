"""Engine REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kodiak.app.engine import get_engine_status, start_engine, stop_engine
from kodiak.errors import AppError
from kodiak.schemas.engine import EngineStatus
from kodiak.utils.config import load_config

router = APIRouter(prefix="/engine")


@router.get("/status", response_model=EngineStatus)
def status():
    """Get engine status."""
    try:
        config = load_config()
        return get_engine_status(config)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


class StartRequest(BaseModel):
    dry_run: bool = False
    interval: int = 60


@router.post("/start")
def start(req: StartRequest):
    """Start the trading engine."""
    try:
        return start_engine(dry_run=req.dry_run, interval=req.interval)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


class StopRequest(BaseModel):
    force: bool = False


@router.post("/stop")
def stop(req: StopRequest):
    """Stop the trading engine."""
    try:
        return stop_engine(force=req.force)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
