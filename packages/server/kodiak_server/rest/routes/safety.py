"""Safety REST API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from kodiak.app.data import get_safety_status
from kodiak.utils.config import load_config

from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/safety")


@router.get("/status")
def status(ctx: RequestContext = Depends(get_request_context)) -> dict[str, Any]:
    """Get safety controls status and configured limits."""
    config = load_config()
    return ok(get_safety_status(config), ctx.request_id)
