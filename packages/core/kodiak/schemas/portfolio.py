"""Portfolio, account, position, and quote schemas."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from kodiak.analysis.allocation import (
        PositionSizingResult,
        RebalancePlan,
        RebalanceTrade,
    )
    from kodiak.analysis.portfolio import (
        EquityCurvePoint,
        PerformanceAttribution,
        PortfolioAnalyticsResult,
        PortfolioConstituentAnalytics,
        PortfolioExposureSummary,
        RollingReturn,
    )
    from kodiak.api.broker import Account, Position, Quote
    from kodiak.core.portfolio import PortfolioSummary, PositionDetail


class AccountInfo(BaseModel):
    """Account information."""

    cash: Decimal
    buying_power: Decimal
    equity: Decimal
    portfolio_value: Decimal
    currency: str = "USD"
    daytrade_count: int = 0
    day_trading_buying_power: Decimal | None = None
    last_equity: Decimal | None = None
    status: str = "ACTIVE"
    pattern_day_trader: bool = False

    @classmethod
    def from_domain(cls, account: Account) -> AccountInfo:
        return cls(
            cash=account.cash,
            buying_power=account.buying_power,
            equity=account.equity,
            portfolio_value=account.portfolio_value,
            currency=account.currency,
            daytrade_count=account.daytrade_count,
            day_trading_buying_power=account.day_trading_buying_power,
            last_equity=account.last_equity,
            status=account.status,
            pattern_day_trader=account.pattern_day_trader,
        )


class PositionInfo(BaseModel):
    """Open position information."""

    symbol: str
    qty: Decimal
    avg_entry_price: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pl: Decimal
    unrealized_pl_pct: Decimal

    @classmethod
    def from_domain(cls, pos: Position) -> PositionInfo:
        return cls(
            symbol=pos.symbol,
            qty=pos.qty,
            avg_entry_price=pos.avg_entry_price,
            current_price=pos.current_price,
            market_value=pos.market_value,
            unrealized_pl=pos.unrealized_pl,
            unrealized_pl_pct=pos.unrealized_pl_pct,
        )


class PositionDetailInfo(BaseModel):
    """Detailed position with weight and cost basis."""

    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    weight_pct: Decimal

    @classmethod
    def from_domain(cls, detail: PositionDetail) -> PositionDetailInfo:
        return cls(
            symbol=detail.symbol,
            quantity=detail.quantity,
            avg_cost=detail.avg_cost,
            current_price=detail.current_price,
            market_value=detail.market_value,
            cost_basis=detail.cost_basis,
            unrealized_pnl=detail.unrealized_pnl,
            unrealized_pnl_pct=detail.unrealized_pnl_pct,
            weight_pct=detail.weight_pct,
        )


class PortfolioResponse(BaseModel):
    """Full portfolio summary."""

    total_equity: Decimal
    cash: Decimal
    positions_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    realized_pnl_today: Decimal
    total_pnl_today: Decimal
    position_count: int
    positions: list[PositionDetailInfo] = []

    @classmethod
    def from_domain(
        cls,
        summary: PortfolioSummary,
        positions: list[PositionDetail] | None = None,
    ) -> PortfolioResponse:

        pos_list = [PositionDetailInfo.from_domain(p) for p in (positions or [])]
        return cls(
            total_equity=summary.total_equity,
            cash=summary.cash,
            positions_value=summary.positions_value,
            unrealized_pnl=summary.unrealized_pnl,
            unrealized_pnl_pct=summary.unrealized_pnl_pct,
            realized_pnl_today=summary.realized_pnl_today,
            total_pnl_today=summary.total_pnl_today,
            position_count=summary.position_count,
            positions=pos_list,
        )


class PortfolioExposureSummaryInfo(BaseModel):
    """Exposure summary for current portfolio holdings."""

    long_exposure: Decimal
    short_exposure: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
    cash_weight_pct: Decimal
    invested_weight_pct: Decimal
    largest_position_weight_pct: Decimal

    @classmethod
    def from_domain(cls, exposure: PortfolioExposureSummary) -> PortfolioExposureSummaryInfo:
        return cls(
            long_exposure=exposure.long_exposure,
            short_exposure=exposure.short_exposure,
            gross_exposure=exposure.gross_exposure,
            net_exposure=exposure.net_exposure,
            cash_weight_pct=exposure.cash_weight_pct,
            invested_weight_pct=exposure.invested_weight_pct,
            largest_position_weight_pct=exposure.largest_position_weight_pct,
        )


class RollingReturnInfo(BaseModel):
    """Trailing return comparison over a fixed window."""

    window_days: int
    portfolio_return_pct: Decimal | None
    benchmark_return_pct: Decimal | None
    excess_return_pct: Decimal | None

    @classmethod
    def from_domain(cls, rolling_return: RollingReturn) -> RollingReturnInfo:
        return cls(
            window_days=rolling_return.window_days,
            portfolio_return_pct=rolling_return.portfolio_return_pct,
            benchmark_return_pct=rolling_return.benchmark_return_pct,
            excess_return_pct=rolling_return.excess_return_pct,
        )


class PortfolioConstituentAnalyticsInfo(BaseModel):
    """Per-position analytics inside the snapshot replay."""

    symbol: str
    quantity: Decimal
    market_value: Decimal
    weight_pct: Decimal
    period_return_pct: Decimal | None
    contribution_pct: Decimal | None

    @classmethod
    def from_domain(
        cls,
        constituent: PortfolioConstituentAnalytics,
    ) -> PortfolioConstituentAnalyticsInfo:
        return cls(
            symbol=constituent.symbol,
            quantity=constituent.quantity,
            market_value=constituent.market_value,
            weight_pct=constituent.weight_pct,
            period_return_pct=constituent.period_return_pct,
            contribution_pct=constituent.contribution_pct,
        )


class EquityCurvePointInfo(BaseModel):
    """One portfolio equity curve observation."""

    timestamp: str
    equity: Decimal
    cash: Decimal
    positions_value: Decimal

    @classmethod
    def from_domain(cls, point: EquityCurvePoint) -> EquityCurvePointInfo:
        return cls(
            timestamp=point.timestamp.isoformat(),
            equity=point.equity,
            cash=point.cash,
            positions_value=point.positions_value,
        )


class PerformanceAttributionInfo(BaseModel):
    """Performance attribution grouped by symbol, rule, or strategy."""

    group_by: str
    key: str
    symbol: str | None
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    contribution_pct: Decimal | None
    trade_count: int
    buy_qty: Decimal
    sell_qty: Decimal

    @classmethod
    def from_domain(cls, attribution: PerformanceAttribution) -> PerformanceAttributionInfo:
        return cls(
            group_by=attribution.group_by,
            key=attribution.key,
            symbol=attribution.symbol,
            realized_pnl=attribution.realized_pnl,
            unrealized_pnl=attribution.unrealized_pnl,
            total_pnl=attribution.total_pnl,
            contribution_pct=attribution.contribution_pct,
            trade_count=attribution.trade_count,
            buy_qty=attribution.buy_qty,
            sell_qty=attribution.sell_qty,
        )


class PortfolioAnalyticsResponse(BaseModel):
    """Portfolio analytics response."""

    generated_at: str
    history_start: str
    history_end: str
    lookback_days: int
    data_source: str
    benchmark_symbol: str
    methodology: str
    total_equity: Decimal
    cash: Decimal
    position_count: int
    trading_days: int
    cumulative_return_pct: Decimal
    benchmark_return_pct: Decimal
    excess_return_pct: Decimal
    annualized_volatility_pct: Decimal | None
    benchmark_volatility_pct: Decimal | None
    sharpe_ratio: Decimal | None
    benchmark_correlation: Decimal | None
    max_drawdown_pct: Decimal
    exposure: PortfolioExposureSummaryInfo
    rolling_returns: list[RollingReturnInfo]
    constituents: list[PortfolioConstituentAnalyticsInfo]
    equity_curve: list[EquityCurvePointInfo] = Field(default_factory=list)
    attribution: list[PerformanceAttributionInfo] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, result: PortfolioAnalyticsResult) -> PortfolioAnalyticsResponse:
        return cls(
            generated_at=result.generated_at.isoformat(),
            history_start=result.history_start.isoformat(),
            history_end=result.history_end.isoformat(),
            lookback_days=result.lookback_days,
            data_source=result.data_source,
            benchmark_symbol=result.benchmark_symbol,
            methodology=result.methodology,
            total_equity=result.total_equity,
            cash=result.cash,
            position_count=result.position_count,
            trading_days=result.trading_days,
            cumulative_return_pct=result.cumulative_return_pct,
            benchmark_return_pct=result.benchmark_return_pct,
            excess_return_pct=result.excess_return_pct,
            annualized_volatility_pct=result.annualized_volatility_pct,
            benchmark_volatility_pct=result.benchmark_volatility_pct,
            sharpe_ratio=result.sharpe_ratio,
            benchmark_correlation=result.benchmark_correlation,
            max_drawdown_pct=result.max_drawdown_pct,
            exposure=PortfolioExposureSummaryInfo.from_domain(result.exposure),
            rolling_returns=[RollingReturnInfo.from_domain(item) for item in result.rolling_returns],
            constituents=[
                PortfolioConstituentAnalyticsInfo.from_domain(item)
                for item in result.constituents
            ],
            equity_curve=[EquityCurvePointInfo.from_domain(item) for item in result.equity_curve],
            attribution=[PerformanceAttributionInfo.from_domain(item) for item in result.attribution],
        )


class PositionSizingRequest(BaseModel):
    """Request for sizing a position."""

    symbol: str
    method: str
    price: Decimal | None = None
    target_value: Decimal | None = None
    target_weight_pct: Decimal | None = None
    risk_budget: Decimal | None = None
    stop_loss_pct: Decimal | None = None
    available_capital: Decimal | None = None
    max_position_value: Decimal | None = None
    max_position_weight_pct: Decimal | None = None
    lot_size: int = 1


class PositionSizingResponse(BaseModel):
    """Calculated target size for a symbol."""

    generated_at: str
    symbol: str
    method: str
    reference_price: Decimal
    current_qty: Decimal
    target_qty: Decimal
    delta_qty: Decimal
    current_position_value: Decimal
    target_position_value: Decimal
    estimated_order_value: Decimal
    estimated_weight_pct: Decimal
    target_weight_pct: Decimal | None
    target_value: Decimal | None
    risk_budget: Decimal | None
    stop_loss_pct: Decimal | None
    capped_by: list[str]

    @classmethod
    def from_domain(cls, result: PositionSizingResult) -> PositionSizingResponse:
        return cls(
            generated_at=result.generated_at.isoformat(),
            symbol=result.symbol,
            method=result.method,
            reference_price=result.reference_price,
            current_qty=result.current_qty,
            target_qty=result.target_qty,
            delta_qty=result.delta_qty,
            current_position_value=result.current_position_value,
            target_position_value=result.target_position_value,
            estimated_order_value=result.estimated_order_value,
            estimated_weight_pct=result.estimated_weight_pct,
            target_weight_pct=result.target_weight_pct,
            target_value=result.target_value,
            risk_budget=result.risk_budget,
            stop_loss_pct=result.stop_loss_pct,
            capped_by=result.capped_by,
        )


class RebalanceRequest(BaseModel):
    """Request for a dry-run rebalance plan."""

    target_weights: dict[str, Decimal]
    drift_threshold_pct: Decimal = Decimal("1")
    cash_buffer_pct: Decimal = Decimal("0")
    liquidate_unmentioned: bool = False
    lot_size: int = 1
    max_position_weight_pct: Decimal | None = None


class RebalanceTradeResponse(BaseModel):
    """One proposed rebalance trade."""

    symbol: str
    side: str
    qty: Decimal
    reference_price: Decimal
    estimated_value: Decimal
    current_qty: Decimal
    target_qty: Decimal
    current_weight_pct: Decimal
    target_weight_pct: Decimal
    drift_pct: Decimal

    @classmethod
    def from_domain(cls, trade: RebalanceTrade) -> RebalanceTradeResponse:
        return cls(
            symbol=trade.symbol,
            side=trade.side,
            qty=trade.qty,
            reference_price=trade.reference_price,
            estimated_value=trade.estimated_value,
            current_qty=trade.current_qty,
            target_qty=trade.target_qty,
            current_weight_pct=trade.current_weight_pct,
            target_weight_pct=trade.target_weight_pct,
            drift_pct=trade.drift_pct,
        )


class RebalancePlanResponse(BaseModel):
    """Dry-run rebalance plan response."""

    generated_at: str
    total_equity: Decimal
    current_cash: Decimal
    projected_cash: Decimal
    current_cash_weight_pct: Decimal
    projected_cash_weight_pct: Decimal
    drift_threshold_pct: Decimal
    cash_buffer_pct: Decimal
    liquidate_unmentioned: bool
    rebalance_required: bool
    trade_count: int
    estimated_turnover_pct: Decimal
    estimated_net_cash_change: Decimal
    target_weights: dict[str, Decimal]
    trades: list[RebalanceTradeResponse]

    @classmethod
    def from_domain(cls, plan: RebalancePlan) -> RebalancePlanResponse:
        return cls(
            generated_at=plan.generated_at.isoformat(),
            total_equity=plan.total_equity,
            current_cash=plan.current_cash,
            projected_cash=plan.projected_cash,
            current_cash_weight_pct=plan.current_cash_weight_pct,
            projected_cash_weight_pct=plan.projected_cash_weight_pct,
            drift_threshold_pct=plan.drift_threshold_pct,
            cash_buffer_pct=plan.cash_buffer_pct,
            liquidate_unmentioned=plan.liquidate_unmentioned,
            rebalance_required=plan.rebalance_required,
            trade_count=plan.trade_count,
            estimated_turnover_pct=plan.estimated_turnover_pct,
            estimated_net_cash_change=plan.estimated_net_cash_change,
            target_weights=plan.target_weights,
            trades=[RebalanceTradeResponse.from_domain(trade) for trade in plan.trades],
        )


class QuoteResponse(BaseModel):
    """Market quote."""

    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    spread: Decimal

    @classmethod
    def from_domain(cls, quote: Quote) -> QuoteResponse:
        return cls(
            symbol=quote.symbol,
            bid=quote.bid,
            ask=quote.ask,
            last=quote.last,
            volume=quote.volume,
            spread=quote.ask - quote.bid,
        )


class BalanceResponse(BaseModel):
    """Balance overview (account + positions + market status)."""

    account: AccountInfo
    positions: list[PositionInfo]
    market_open: bool
    total_positions_value: Decimal
    total_unrealized_pl: Decimal
    day_change: Decimal | None = None
    day_change_pct: Decimal | None = None
