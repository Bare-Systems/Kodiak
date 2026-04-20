"""Engine REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from kodiak.app.engine import get_engine_status, start_engine, stop_engine
from kodiak.utils.config import load_config
from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/engine")


@router.get("/status")
def status(ctx: RequestContext = Depends(get_request_context)):
    """Get engine status."""
    config = load_config()
    return ok(get_engine_status(config), ctx.request_id)


class StartRequest(BaseModel):
    dry_run: bool = False
    interval: int = 60


@router.post("/start")
def start(req: StartRequest, ctx: RequestContext = Depends(get_request_context)):
    """Start the trading engine."""
    return ok(start_engine(dry_run=req.dry_run, interval=req.interval), ctx.request_id)


class StopRequest(BaseModel):
    force: bool = False


@router.post("/stop")
def stop(req: StopRequest, ctx: RequestContext = Depends(get_request_context)):
    """Stop the trading engine."""
    return ok(stop_engine(force=req.force), ctx.request_id)
