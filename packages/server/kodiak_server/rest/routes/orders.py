"""Orders REST API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from kodiak.app.orders import cancel_order, list_orders, place_order
from kodiak.utils.config import load_config
from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/orders")


class PlaceOrderRequest(BaseModel):
    symbol: str
    qty: int
    side: str = "buy"
    price: float | None = None


@router.post("/")
def create_order(
    req: PlaceOrderRequest,
    ctx: RequestContext = Depends(get_request_context),
):
    """Place an order."""
    config = load_config()
    return ok(
        place_order(config, symbol=req.symbol, qty=req.qty, side=req.side, price=req.price),
        ctx.request_id,
    )


@router.get("/")
def get_orders(
    show_all: bool = Query(False),
    ctx: RequestContext = Depends(get_request_context),
):
    """List orders."""
    config = load_config()
    return ok(list_orders(config, show_all=show_all), ctx.request_id)


@router.delete("/{order_id}")
def delete_order(order_id: str, ctx: RequestContext = Depends(get_request_context)):
    """Cancel an order."""
    config = load_config()
    return ok(cancel_order(config, order_id=order_id), ctx.request_id)
