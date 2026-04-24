"""Research data schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from kodiak.data.research import FundamentalRecord


class FundamentalsResponse(BaseModel):
    """Company fundamentals for one symbol."""

    symbol: str
    source: str
    as_of: str | None = None
    currency: str | None = None
    market_cap: Decimal | None = None
    enterprise_value: Decimal | None = None
    pe_ratio: Decimal | None = None
    forward_pe_ratio: Decimal | None = None
    price_to_sales: Decimal | None = None
    price_to_book: Decimal | None = None
    dividend_yield_pct: Decimal | None = None
    beta: Decimal | None = None
    eps_ttm: Decimal | None = None
    revenue_ttm: Decimal | None = None
    gross_margin_pct: Decimal | None = None
    operating_margin_pct: Decimal | None = None
    profit_margin_pct: Decimal | None = None
    debt_to_equity: Decimal | None = None
    return_on_equity_pct: Decimal | None = None
    free_cash_flow: Decimal | None = None
    shares_outstanding: Decimal | None = None
    metadata: dict[str, Any] = {}

    @classmethod
    def from_domain(cls, record: FundamentalRecord) -> FundamentalsResponse:
        return cls(
            symbol=record.symbol,
            source=record.source,
            as_of=record.as_of,
            currency=record.currency,
            market_cap=record.market_cap,
            enterprise_value=record.enterprise_value,
            pe_ratio=record.pe_ratio,
            forward_pe_ratio=record.forward_pe_ratio,
            price_to_sales=record.price_to_sales,
            price_to_book=record.price_to_book,
            dividend_yield_pct=record.dividend_yield_pct,
            beta=record.beta,
            eps_ttm=record.eps_ttm,
            revenue_ttm=record.revenue_ttm,
            gross_margin_pct=record.gross_margin_pct,
            operating_margin_pct=record.operating_margin_pct,
            profit_margin_pct=record.profit_margin_pct,
            debt_to_equity=record.debt_to_equity,
            return_on_equity_pct=record.return_on_equity_pct,
            free_cash_flow=record.free_cash_flow,
            shares_outstanding=record.shares_outstanding,
            metadata=record.metadata,
        )


class BenchmarkBarResponse(BaseModel):
    """One historical benchmark bar."""

    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class BenchmarkHistoryResponse(BaseModel):
    """Historical benchmark price series."""

    generated_at: str
    symbol: str
    data_source: str
    timeframe: str
    start: str
    end: str
    bar_count: int
    first_close: Decimal
    latest_close: Decimal
    return_pct: Decimal
    bars: list[BenchmarkBarResponse]
