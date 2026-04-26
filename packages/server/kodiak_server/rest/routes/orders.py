"""Orders REST API routes."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from kodiak.app.orders import cancel_order, list_orders, place_order
from kodiak.schemas.orders import OrderRequest
from kodiak.utils.config import load_config
from pydantic import BaseModel

from kodiak_server.rest.context import RequestContext, get_request_context
from kodiak_server.rest.response import ok

router = APIRouter(prefix="/orders")


class PlaceOrderRequest(BaseModel):
    symbol: str
    qty: int
    side: str = "buy"
    price: float
    confirm_execution: bool = False


@router.post("/")
def create_order(
    req: PlaceOrderRequest,
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Place an order."""
    config = load_config()
    return ok(
        place_order(
            config,
            OrderRequest(
                symbol=req.symbol,
                qty=req.qty,
                side=req.side,
                price=Decimal(str(req.price)),
            ),
            confirm_execution=req.confirm_execution,
        ),
        ctx.request_id,
    )


@router.get("/")
def get_orders(
    show_all: bool = Query(False),
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """List orders."""
    config = load_config()
    return ok(list_orders(config, show_all=show_all), ctx.request_id)


@router.delete("/{order_id}")
def delete_order(
    order_id: str,
    confirm_execution: bool = Query(False),
    ctx: RequestContext = Depends(get_request_context),
) -> dict[str, Any]:
    """Cancel an order."""
    config = load_config()
    return ok(
        cancel_order(config, order_id=order_id, confirm_execution=confirm_execution),
        ctx.request_id,
    )
