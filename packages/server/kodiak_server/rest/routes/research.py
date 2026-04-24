"""Research data REST API routes."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from kodiak.app.research import get_benchmark_history, get_fundamentals
from kodiak.data.providers.base import TimeFrame
from kodiak.utils.config import load_config

from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/research")


@router.get("/fundamentals/{symbol}")
def fundamentals(
    symbol: str,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Get company fundamentals for a symbol."""
    config = load_config()
    return ok(get_fundamentals(config, symbol), ctx.request_id)


@router.get("/benchmark/{symbol}")
def benchmark_history(
    symbol: str,
    start: date = Query(...),
    end: date = Query(...),
    data_source: str | None = Query(None),
    timeframe: TimeFrame = Query(TimeFrame.DAY_1),
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Get historical bars and return stats for a benchmark symbol."""
    config = load_config()
    return ok(
        get_benchmark_history(
            config,
            symbol,
            start=start,
            end=end,
            data_source=data_source,
            timeframe=timeframe,
        ),
        ctx.request_id,
    )
