"""Backtest request and response schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from kodiak.backtest.results import BacktestResult


class FeeModel(BaseModel):
    """Transaction fee model for backtest execution."""

    type: Literal["fixed", "percentage"] = "fixed"
    value: float = Field(default=0.0, ge=0.0)
    # fixed: dollar amount per order; percentage: fraction of notional (e.g. 0.001 = 0.1%)


class SlippageModel(BaseModel):
    """Slippage model for backtest execution."""

    type: Literal["fixed_bps", "volatility_bps"] = "fixed_bps"
    bps: float = Field(default=0.0, ge=0.0)
    # fixed_bps: constant basis points; volatility_bps: bps scaled by bar range / close


class FillModel(BaseModel):
    """Fill behavior model for backtest execution."""

    type: Literal["full", "partial"] = "full"
    partial_pct: float = Field(default=1.0, ge=0.01, le=1.0)
    # partial: fill only partial_pct of order qty (deterministic)


class ExecutionConfig(BaseModel):
    """Configurable execution realism for backtests.

    Defaults produce zero-cost, full-fill, zero-slippage behavior (backward-compatible).
    """

    fee: FeeModel = Field(default_factory=FeeModel)
    slippage: SlippageModel = Field(default_factory=SlippageModel)
    fill: FillModel = Field(default_factory=FillModel)


class BacktestRequest(BaseModel):
    """Input for running a backtest.

    Accepts either a single `symbol` (legacy) or a list of `symbols` (preferred).
    When `symbols` contains more than one entry the orchestrator runs per-symbol
    backtests with equally-split capital and returns a PortfolioBacktestResponse.
    """

    strategy_type: str  # trailing-stop, bracket
    symbol: str | None = None  # legacy single-symbol; prefer `symbols`
    symbols: list[str] | None = None  # multi-symbol; takes precedence when set
    start: str  # YYYY-MM-DD
    end: str  # YYYY-MM-DD
    qty: int = Field(ge=1, default=10)
    trailing_pct: float | None = None
    take_profit: float | None = None
    stop_loss: float | None = None
    data_source: str = "csv"
    data_dir: str | None = None
    initial_capital: float = Field(default=100000.0, gt=0)
    save: bool = True
    execution: ExecutionConfig | None = None

    @model_validator(mode="after")
    def normalize_symbols(self) -> BacktestRequest:
        if not self.symbols and not self.symbol:
            raise ValueError("At least one of 'symbol' or 'symbols' must be provided")
        if self.symbols is not None:
            self.symbols = [s.upper() for s in self.symbols]
        if self.symbol is not None:
            self.symbol = self.symbol.upper()
        return self

    def get_symbols(self) -> list[str]:
        """Return the normalized list of symbols to backtest."""
        if self.symbols:
            return self.symbols
        return [self.symbol] if self.symbol else []


class BacktestSummary(BaseModel):
    """Metadata-level view for listing backtests."""

    id: str
    strategy_type: str
    symbol: str
    start_date: str
    end_date: str
    total_return_pct: Decimal
    win_rate: Decimal
    total_trades: int
    max_drawdown_pct: Decimal
    created_at: str
    position_state: str = "unknown"
    strategy_signature: str | None = None
    duplicate_group_size: int = 1
    duplicate_rank: int = 1

    @classmethod
    def from_index_entry(cls, entry: dict[str, Any]) -> BacktestSummary:
        """Create from a backtest index entry dict."""
        return cls(
            id=entry["id"],
            strategy_type=entry["strategy_type"],
            symbol=entry["symbol"],
            start_date=entry["start_date"],
            end_date=entry["end_date"],
            total_return_pct=Decimal(entry["total_return_pct"]),
            win_rate=Decimal(entry["win_rate"]),
            total_trades=entry["total_trades"],
            max_drawdown_pct=Decimal(entry["max_drawdown_pct"]),
            created_at=entry["created_at"],
            position_state=entry.get("position_state", "unknown"),
            strategy_signature=entry.get("strategy_signature"),
            duplicate_group_size=entry.get("duplicate_group_size", 1),
            duplicate_rank=entry.get("duplicate_rank", 1),
        )


class BacktestResponse(BaseModel):
    """Full backtest result."""

    id: str
    strategy_type: str
    symbol: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    strategy_config: dict[str, Any]
    initial_capital: Decimal
    # Performance metrics (net of fees)
    total_return: Decimal
    total_return_pct: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    max_drawdown_pct: Decimal
    sharpe_ratio: Decimal | None = None
    # Execution cost metrics
    total_fees_paid: Decimal = Decimal("0")
    gross_return: Decimal = Decimal("0")
    gross_return_pct: Decimal = Decimal("0")
    execution_config: dict[str, Any] | None = None
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: Decimal = Decimal("0")
    avg_loss: Decimal = Decimal("0")
    largest_win: Decimal = Decimal("0")
    largest_loss: Decimal = Decimal("0")
    # Time series
    equity_curve: list[tuple[str, str]] = []
    trades: list[dict[str, Any]] = []

    @classmethod
    def from_domain(cls, r: BacktestResult) -> BacktestResponse:
        return cls(
            id=r.id,
            strategy_type=r.strategy_type,
            symbol=r.symbol,
            start_date=r.start_date,
            end_date=r.end_date,
            created_at=r.created_at,
            strategy_config=r.strategy_config,
            initial_capital=r.initial_capital,
            total_return=r.total_return,
            total_return_pct=r.total_return_pct,
            win_rate=r.win_rate,
            profit_factor=r.profit_factor,
            max_drawdown=r.max_drawdown,
            max_drawdown_pct=r.max_drawdown_pct,
            sharpe_ratio=r.sharpe_ratio,
            total_fees_paid=r.total_fees_paid,
            gross_return=r.gross_return,
            gross_return_pct=r.gross_return_pct,
            execution_config=r.execution_config,
            total_trades=r.total_trades,
            winning_trades=r.winning_trades,
            losing_trades=r.losing_trades,
            avg_win=r.avg_win,
            avg_loss=r.avg_loss,
            largest_win=r.largest_win,
            largest_loss=r.largest_loss,
            equity_curve=[
                (ts.isoformat(), str(equity)) for ts, equity in r.equity_curve
            ],
            trades=r.trades,
        )


class PortfolioSymbolSummary(BaseModel):
    """Per-symbol attribution within a portfolio backtest."""

    symbol: str
    backtest_id: str
    allocation: Decimal
    total_return: Decimal
    total_return_pct: Decimal
    gross_return_pct: Decimal
    total_fees_paid: Decimal
    win_rate: Decimal
    total_trades: int
    max_drawdown_pct: Decimal


class PortfolioBacktestResponse(BaseModel):
    """Multi-symbol portfolio backtest result.

    Returned when BacktestRequest.symbols contains more than one ticker.
    Capital is split equally across symbols; each symbol runs as an
    independent backtest and results are aggregated here.
    """

    id: str
    strategy_type: str
    symbols: list[str]
    start_date: datetime
    end_date: datetime
    created_at: datetime
    initial_capital: Decimal
    execution_config: dict[str, Any] | None = None
    # Portfolio-level summary (equal-weight aggregation across symbols)
    portfolio_return_pct: Decimal
    portfolio_gross_return_pct: Decimal
    portfolio_total_fees_paid: Decimal
    portfolio_max_drawdown_pct: Decimal
    portfolio_win_rate: Decimal
    total_trades: int
    # Per-symbol detail
    symbol_results: list[BacktestResponse]
    symbol_attribution: list[PortfolioSymbolSummary]
