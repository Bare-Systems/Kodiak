"""Analysis report REST routes."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends
from kodiak.app.reports import export_analysis_report
from kodiak.utils.config import load_config
from pydantic import BaseModel, Field

from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/reports")


class AnalysisReportRequest(BaseModel):
    """Request body for a headless analysis report."""

    format: Literal["json", "markdown"] = "json"
    symbol: str | None = None
    days: int = Field(30, ge=1)
    limit: int = Field(1000, ge=1)
    include_portfolio: bool = False
    portfolio_lookback_days: int = Field(252, ge=1)
    benchmark_symbol: str = "SPY"


@router.post("/analysis")
def analysis_report(
    request: AnalysisReportRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Generate a headless analysis report without writing server-side files."""
    config = load_config()
    result = export_analysis_report(
        config,
        output_path=None,
        format=request.format,
        symbol=request.symbol,
        days=request.days,
        limit=request.limit,
        include_portfolio=request.include_portfolio,
        portfolio_lookback_days=request.portfolio_lookback_days,
        benchmark_symbol=request.benchmark_symbol,
    )
    return ok(result, ctx.request_id)
