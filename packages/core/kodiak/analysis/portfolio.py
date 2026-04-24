"""Portfolio analytics derived from a current holdings snapshot."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pandas as pd

from kodiak.api.broker import Account, Position

SNAPSHOT_METHODOLOGY = (
    "Estimated from the current portfolio snapshot by replaying current holdings "
    "against historical close data; past cash flows and historical rebalances are "
    "not reconstructed."
)


def _to_decimal(value: float | int, places: int = 6) -> Decimal:
    """Convert numeric values into stable Decimal strings for API output."""
    return Decimal(f"{float(value):.{places}f}")


@dataclass
class PortfolioExposureSummary:
    """Current exposure summary."""

    long_exposure: Decimal
    short_exposure: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
    cash_weight_pct: Decimal
    invested_weight_pct: Decimal
    largest_position_weight_pct: Decimal


@dataclass
class RollingReturn:
    """Trailing return for a fixed lookback window."""

    window_days: int
    portfolio_return_pct: Decimal | None
    benchmark_return_pct: Decimal | None
    excess_return_pct: Decimal | None


@dataclass
class PortfolioConstituentAnalytics:
    """Per-position analytics across the replayed history."""

    symbol: str
    quantity: Decimal
    market_value: Decimal
    weight_pct: Decimal
    period_return_pct: Decimal | None
    contribution_pct: Decimal | None


@dataclass
class PortfolioAnalyticsResult:
    """Snapshot-based portfolio analytics result."""

    generated_at: datetime
    history_start: datetime
    history_end: datetime
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
    exposure: PortfolioExposureSummary
    rolling_returns: list[RollingReturn]
    constituents: list[PortfolioConstituentAnalytics]


def compute_portfolio_analytics(
    *,
    account: Account,
    positions: list[Position],
    price_history: dict[str, pd.DataFrame],
    benchmark_symbol: str,
    data_source: str,
    lookback_days: int,
    generated_at: datetime | None = None,
) -> PortfolioAnalyticsResult:
    """Compute portfolio analytics from a current portfolio snapshot."""
    generated_at = generated_at or datetime.now()

    benchmark_df = price_history[benchmark_symbol]
    benchmark_series = benchmark_df["close"].rename(benchmark_symbol)

    position_frames: list[pd.Series] = []
    for position in positions:
        history = price_history[position.symbol]["close"].rename(position.symbol)
        position_frames.append(history)

    aligned_prices = pd.concat([*position_frames, benchmark_series], axis=1, join="inner").dropna()
    if aligned_prices.empty:
        raise ValueError("No overlapping historical data was found for the portfolio and benchmark.")

    required_rows = max(2, lookback_days + 1)
    if len(aligned_prices) < 2:
        raise ValueError("At least two aligned price observations are required for analytics.")
    if len(aligned_prices) > required_rows:
        aligned_prices = aligned_prices.iloc[-required_rows:]

    history_start = aligned_prices.index[0].to_pydatetime()
    history_end = aligned_prices.index[-1].to_pydatetime()

    portfolio_values = pd.Series(float(account.cash), index=aligned_prices.index, dtype="float64")
    for position in positions:
        portfolio_values = portfolio_values.add(
            aligned_prices[position.symbol] * float(position.qty),
            fill_value=float(account.cash),
        )

    benchmark_prices = aligned_prices[benchmark_symbol]
    portfolio_returns = portfolio_values.pct_change().dropna()
    benchmark_returns = benchmark_prices.pct_change().dropna()
    aligned_returns = pd.concat(
        [
            portfolio_returns.rename("portfolio"),
            benchmark_returns.rename("benchmark"),
        ],
        axis=1,
        join="inner",
    ).dropna()

    cumulative_return_pct = _calculate_total_return_pct(portfolio_values)
    benchmark_return_pct = _calculate_total_return_pct(benchmark_prices)
    excess_return_pct = cumulative_return_pct - benchmark_return_pct
    max_drawdown_pct = _calculate_max_drawdown_pct(portfolio_values)

    sharpe_ratio = None
    annualized_volatility_pct = None
    benchmark_volatility_pct = None
    benchmark_correlation = None
    if not portfolio_returns.empty:
        portfolio_std = float(portfolio_returns.std())
        annualized_volatility_pct = _to_decimal(portfolio_std * math.sqrt(252) * 100)
        if portfolio_std > 0:
            sharpe_ratio = _to_decimal(
                float(portfolio_returns.mean()) / portfolio_std * math.sqrt(252)
            )
    if not benchmark_returns.empty:
        benchmark_volatility_pct = _to_decimal(float(benchmark_returns.std()) * math.sqrt(252) * 100)
    if len(aligned_returns) >= 2:
        portfolio_corr_std = float(aligned_returns["portfolio"].std())
        benchmark_corr_std = float(aligned_returns["benchmark"].std())
        if portfolio_corr_std > 0 and benchmark_corr_std > 0:
            correlation = aligned_returns["portfolio"].corr(aligned_returns["benchmark"])
            if pd.notna(correlation):
                benchmark_correlation = _to_decimal(float(correlation))

    total_equity = account.equity
    long_exposure = sum((max(position.market_value, Decimal("0")) for position in positions), Decimal("0"))
    short_exposure = sum(
        (abs(min(position.market_value, Decimal("0"))) for position in positions),
        Decimal("0"),
    )
    gross_exposure = long_exposure + short_exposure
    net_exposure = long_exposure - short_exposure
    cash_weight_pct = (account.cash / total_equity * 100) if total_equity else Decimal("0")
    invested_weight_pct = (gross_exposure / total_equity * 100) if total_equity else Decimal("0")
    largest_position_weight_pct = max(
        ((abs(position.market_value) / total_equity * 100) for position in positions),
        default=Decimal("0"),
    )

    start_portfolio_value = float(portfolio_values.iloc[0])
    constituents: list[PortfolioConstituentAnalytics] = []
    for position in sorted(positions, key=lambda item: item.market_value, reverse=True):
        symbol_prices = aligned_prices[position.symbol]
        symbol_return_pct: Decimal | None = _calculate_total_return_pct(symbol_prices)
        contribution_pct: Decimal | None = None
        if start_portfolio_value > 0:
            start_value = float(symbol_prices.iloc[0]) * float(position.qty)
            end_value = float(symbol_prices.iloc[-1]) * float(position.qty)
            contribution_pct = _to_decimal(((end_value - start_value) / start_portfolio_value) * 100)

        constituents.append(
            PortfolioConstituentAnalytics(
                symbol=position.symbol,
                quantity=position.qty,
                market_value=position.market_value,
                weight_pct=((position.market_value / total_equity) * 100) if total_equity else Decimal("0"),
                period_return_pct=symbol_return_pct,
                contribution_pct=contribution_pct,
            )
        )

    rolling_returns = [
        _build_rolling_return(window, portfolio_values, benchmark_prices)
        for window in (5, 21, 63, 126, 252)
    ]

    return PortfolioAnalyticsResult(
        generated_at=generated_at,
        history_start=history_start,
        history_end=history_end,
        lookback_days=min(lookback_days, max(len(aligned_prices) - 1, 1)),
        data_source=data_source,
        benchmark_symbol=benchmark_symbol,
        methodology=SNAPSHOT_METHODOLOGY,
        total_equity=account.equity,
        cash=account.cash,
        position_count=len(positions),
        trading_days=max(len(aligned_prices) - 1, 0),
        cumulative_return_pct=cumulative_return_pct,
        benchmark_return_pct=benchmark_return_pct,
        excess_return_pct=excess_return_pct,
        annualized_volatility_pct=annualized_volatility_pct,
        benchmark_volatility_pct=benchmark_volatility_pct,
        sharpe_ratio=sharpe_ratio,
        benchmark_correlation=benchmark_correlation,
        max_drawdown_pct=max_drawdown_pct,
        exposure=PortfolioExposureSummary(
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            cash_weight_pct=cash_weight_pct,
            invested_weight_pct=invested_weight_pct,
            largest_position_weight_pct=largest_position_weight_pct,
        ),
        rolling_returns=rolling_returns,
        constituents=constituents,
    )


def _calculate_total_return_pct(series: pd.Series) -> Decimal:
    """Calculate total percent return across a price/value series."""
    start_value = float(series.iloc[0])
    end_value = float(series.iloc[-1])
    if start_value <= 0:
        return Decimal("0")
    return _to_decimal(((end_value / start_value) - 1) * 100)


def _calculate_max_drawdown_pct(series: pd.Series) -> Decimal:
    """Calculate max drawdown percentage from a portfolio value series."""
    running_peak = series.cummax()
    drawdown = (series / running_peak) - 1
    min_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
    return _to_decimal(abs(min_drawdown) * 100)


def _build_rolling_return(
    window_days: int,
    portfolio_values: pd.Series,
    benchmark_prices: pd.Series,
) -> RollingReturn:
    """Build a trailing return comparison for a fixed window."""
    if len(portfolio_values) <= window_days:
        return RollingReturn(
            window_days=window_days,
            portfolio_return_pct=None,
            benchmark_return_pct=None,
            excess_return_pct=None,
        )

    portfolio_return_pct = _to_decimal(
        ((float(portfolio_values.iloc[-1]) / float(portfolio_values.iloc[-window_days - 1])) - 1) * 100
    )
    benchmark_return_pct = _to_decimal(
        ((float(benchmark_prices.iloc[-1]) / float(benchmark_prices.iloc[-window_days - 1])) - 1) * 100
    )
    return RollingReturn(
        window_days=window_days,
        portfolio_return_pct=portfolio_return_pct,
        benchmark_return_pct=benchmark_return_pct,
        excess_return_pct=portfolio_return_pct - benchmark_return_pct,
    )
