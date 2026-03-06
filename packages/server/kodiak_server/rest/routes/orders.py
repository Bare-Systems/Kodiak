"""Orders REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from kodiak.app.orders import cancel_order, list_orders, place_order
from kodiak.errors import AppError
from kodiak.utils.config import load_config

router = APIRouter(prefix="/orders")


class PlaceOrderRequest(BaseModel):
    symbol: str
    qty: int
    side: str = "buy"
    price: float | None = None


@router.post("/")
def create_order(req: PlaceOrderRequest):
    """Place an order."""
    try:
        config = load_config()
        return place_order(
            config, symbol=req.symbol, qty=req.qty, side=req.side, price=req.price
        )
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/")
def get_orders(show_all: bool = Query(False)):
    """List orders."""
    try:
        config = load_config()
        return list_orders(config, show_all=show_all)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.delete("/{order_id}")
def delete_order(order_id: str):
    """Cancel an order."""
    try:
        config = load_config()
        return cancel_order(config, order_id=order_id)
    except AppError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
