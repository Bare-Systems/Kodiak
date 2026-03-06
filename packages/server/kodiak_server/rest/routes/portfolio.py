"""Portfolio REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from kodiak.app.portfolio import (
    get_balance,
    get_portfolio_summary,
    get_positions,
    get_quote,
    get_top_movers,
)
from kodiak.errors import AppError
from kodiak.utils.config import load_config

router = APIRouter(prefix="/portfolio")


@router.get("/balance")
def balance():
    """Get account balance."""
    try:
        config = load_config()
        return get_balance(config)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/positions")
def positions():
    """Get open positions."""
    try:
        config = load_config()
        return get_positions(config)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/summary")
def summary():
    """Get full portfolio summary."""
    try:
        config = load_config()
        return get_portfolio_summary(config)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/quote/{symbol}")
def quote(symbol: str):
    """Get a quote for a symbol."""
    try:
        config = load_config()
        return get_quote(config, symbol)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/movers")
def movers(market_type: str = Query("stocks"), limit: int = Query(10)):
    """Get top movers."""
    try:
        config = load_config()
        return get_top_movers(config, market_type=market_type, limit=limit)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
