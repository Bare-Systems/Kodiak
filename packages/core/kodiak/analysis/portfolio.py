"""Portfolio analytics derived from current holdings or trade history."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal

import pandas as pd

from kodiak.api.broker import Account, Position
from kodiak.data.ledger import TradeRecord

SNAPSHOT_METHODOLOGY = (
    "Estimated from the current portfolio snapshot by replaying current holdings "
    "against historical close data; past cash flows and historical rebalances are "
    "not reconstructed."
)
TRANSACTION_METHODOLOGY = (
    "Reconstructed from trade ledger transactions, current cash, current positions, "
    "and historical close data. Assumes no external cash flows, dividends, or fees "
    "inside the lookback window."
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
    """Per-symbol analytics across the replayed history."""

    symbol: str
    quantity: Decimal
    market_value: Decimal
    weight_pct: Decimal
    period_return_pct: Decimal | None
    contribution_pct: Decimal | None


@dataclass
class EquityCurvePoint:
    """One portfolio equity observation."""

    timestamp: datetime
    equity: Decimal
    cash: Decimal
    positions_value: Decimal


@dataclass
class PortfolioAnalyticsResult:
    """Portfolio analytics result."""

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
    equity_curve: list[EquityCurvePoint]


@dataclass
class _SeriesMetrics:
    cumulative_return_pct: Decimal
    benchmark_return_pct: Decimal
    excess_return_pct: Decimal
    annualized_volatility_pct: Decimal | None
    benchmark_volatility_pct: Decimal | None
    sharpe_ratio: Decimal | None
    benchmark_correlation: Decimal | None
    max_drawdown_pct: Decimal


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
    benchmark_series = price_history[benchmark_symbol]["close"].rename(benchmark_symbol)
    position_frames = [
        price_history[position.symbol]["close"].rename(position.symbol)
        for position in positions
    ]

    aligned_prices = _align_price_history([*position_frames, benchmark_series], lookback_days)
    history_start = aligned_prices.index[0].to_pydatetime()
    history_end = aligned_prices.index[-1].to_pydatetime()

    portfolio_values = pd.Series(float(account.cash), index=aligned_prices.index, dtype="float64")
    positions_values = pd.Series(0.0, index=aligned_prices.index, dtype="float64")
    for position in positions:
        value_series = aligned_prices[position.symbol] * float(position.qty)
        portfolio_values = portfolio_values.add(value_series, fill_value=float(account.cash))
        positions_values = positions_values.add(value_series, fill_value=0.0)

    benchmark_prices = aligned_prices[benchmark_symbol]
    metrics = _calculate_series_metrics(portfolio_values, benchmark_prices)
    exposure = _build_exposure(account, positions)
    constituents = _build_snapshot_constituents(
        account=account,
        positions=positions,
        aligned_prices=aligned_prices,
        portfolio_values=portfolio_values,
    )

    return _build_result(
        account=account,
        positions=positions,
        generated_at=generated_at,
        history_start=history_start,
        history_end=history_end,
        aligned_prices=aligned_prices,
        benchmark_prices=benchmark_prices,
        data_source=data_source,
        benchmark_symbol=benchmark_symbol,
        methodology=SNAPSHOT_METHODOLOGY,
        metrics=metrics,
        exposure=exposure,
        constituents=constituents,
        portfolio_values=portfolio_values,
        cash_values=pd.Series(float(account.cash), index=portfolio_values.index, dtype="float64"),
        positions_values=positions_values,
        lookback_days=lookback_days,
    )


def compute_transaction_portfolio_analytics(
    *,
    account: Account,
    positions: list[Position],
    trades: list[TradeRecord],
    price_history: dict[str, pd.DataFrame],
    benchmark_symbol: str,
    data_source: str,
    lookback_days: int,
    generated_at: datetime | None = None,
) -> PortfolioAnalyticsResult:
    """Compute portfolio analytics by replaying trade ledger transactions.

    Current cash and positions are used as the endpoint, then trades inside the
    aligned lookback window are reversed to infer starting cash and shares.
    """
    generated_at = generated_at or datetime.now()
    position_by_symbol = {position.symbol.upper(): position for position in positions}
    symbols = sorted(set(position_by_symbol) | {trade.symbol.upper() for trade in trades})
    if not symbols:
        return compute_portfolio_analytics(
            account=account,
            positions=positions,
            price_history=price_history,
            benchmark_symbol=benchmark_symbol,
            data_source=data_source,
            lookback_days=lookback_days,
            generated_at=generated_at,
        )

    price_frames = [price_history[symbol]["close"].rename(symbol) for symbol in symbols]
    benchmark_series = price_history[benchmark_symbol]["close"].rename(benchmark_symbol)
    aligned_prices = _align_price_history([*price_frames, benchmark_series], lookback_days)
    history_start = aligned_prices.index[0].to_pydatetime()
    history_end = aligned_prices.index[-1].to_pydatetime()

    in_window_trades = [
        trade
        for trade in trades
        if _as_naive(trade.timestamp) >= datetime.combine(history_start.date(), time.min)
        and _as_naive(trade.timestamp) <= datetime.combine(history_end.date(), time.max)
    ]
    in_window_trades.sort(key=lambda trade: trade.timestamp)

    current_qty = {
        symbol: position_by_symbol[symbol].qty if symbol in position_by_symbol else Decimal("0")
        for symbol in symbols
    }
    start_qty = current_qty.copy()
    start_cash = account.cash
    for trade in in_window_trades:
        symbol = trade.symbol.upper()
        if trade.is_buy:
            start_qty[symbol] -= trade.quantity
            start_cash += trade.total
        elif trade.is_sell:
            start_qty[symbol] += trade.quantity
            start_cash -= trade.total

    cash = start_cash
    holdings = start_qty.copy()
    trade_index = 0
    portfolio_values: list[float] = []
    cash_values: list[float] = []
    positions_values: list[float] = []

    for timestamp, row in aligned_prices.iterrows():
        day_end = datetime.combine(timestamp.to_pydatetime().date(), time.max)
        while (
            trade_index < len(in_window_trades)
            and _as_naive(in_window_trades[trade_index].timestamp) <= day_end
        ):
            trade = in_window_trades[trade_index]
            symbol = trade.symbol.upper()
            if trade.is_buy:
                holdings[symbol] += trade.quantity
                cash -= trade.total
            elif trade.is_sell:
                holdings[symbol] -= trade.quantity
                cash += trade.total
            trade_index += 1

        positions_value = Decimal("0")
        for symbol in symbols:
            positions_value += holdings[symbol] * Decimal(str(row[symbol]))
        equity = cash + positions_value
        portfolio_values.append(float(equity))
        cash_values.append(float(cash))
        positions_values.append(float(positions_value))

    portfolio_series = pd.Series(portfolio_values, index=aligned_prices.index, dtype="float64")
    cash_series = pd.Series(cash_values, index=aligned_prices.index, dtype="float64")
    positions_series = pd.Series(positions_values, index=aligned_prices.index, dtype="float64")
    benchmark_prices = aligned_prices[benchmark_symbol]
    metrics = _calculate_series_metrics(portfolio_series, benchmark_prices)
    exposure = _build_exposure(account, positions)
    constituents = _build_transaction_constituents(
        account=account,
        positions=positions,
        symbols=symbols,
        start_qty=start_qty,
        end_qty=holdings,
        trades=in_window_trades,
        aligned_prices=aligned_prices,
        start_equity=Decimal(str(portfolio_series.iloc[0])),
    )

    return _build_result(
        account=account,
        positions=positions,
        generated_at=generated_at,
        history_start=history_start,
        history_end=history_end,
        aligned_prices=aligned_prices,
        benchmark_prices=benchmark_prices,
        data_source=data_source,
        benchmark_symbol=benchmark_symbol,
        methodology=TRANSACTION_METHODOLOGY,
        metrics=metrics,
        exposure=exposure,
        constituents=constituents,
        portfolio_values=portfolio_series,
        cash_values=cash_series,
        positions_values=positions_series,
        lookback_days=lookback_days,
    )


def _align_price_history(series: list[pd.Series], lookback_days: int) -> pd.DataFrame:
    aligned_prices = pd.concat(series, axis=1, join="inner").dropna()
    if aligned_prices.empty:
        raise ValueError("No overlapping historical data was found for the portfolio and benchmark.")
    if len(aligned_prices) < 2:
        raise ValueError("At least two aligned price observations are required for analytics.")
    required_rows = max(2, lookback_days + 1)
    if len(aligned_prices) > required_rows:
        aligned_prices = aligned_prices.iloc[-required_rows:]
    return aligned_prices


def _calculate_series_metrics(
    portfolio_values: pd.Series,
    benchmark_prices: pd.Series,
) -> _SeriesMetrics:
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

    return _SeriesMetrics(
        cumulative_return_pct=cumulative_return_pct,
        benchmark_return_pct=benchmark_return_pct,
        excess_return_pct=cumulative_return_pct - benchmark_return_pct,
        annualized_volatility_pct=annualized_volatility_pct,
        benchmark_volatility_pct=benchmark_volatility_pct,
        sharpe_ratio=sharpe_ratio,
        benchmark_correlation=benchmark_correlation,
        max_drawdown_pct=_calculate_max_drawdown_pct(portfolio_values),
    )


def _build_exposure(account: Account, positions: list[Position]) -> PortfolioExposureSummary:
    total_equity = account.equity
    long_exposure = sum((max(position.market_value, Decimal("0")) for position in positions), Decimal("0"))
    short_exposure = sum(
        (abs(min(position.market_value, Decimal("0"))) for position in positions),
        Decimal("0"),
    )
    gross_exposure = long_exposure + short_exposure
    return PortfolioExposureSummary(
        long_exposure=long_exposure,
        short_exposure=short_exposure,
        gross_exposure=gross_exposure,
        net_exposure=long_exposure - short_exposure,
        cash_weight_pct=(account.cash / total_equity * 100) if total_equity else Decimal("0"),
        invested_weight_pct=(gross_exposure / total_equity * 100) if total_equity else Decimal("0"),
        largest_position_weight_pct=max(
            ((abs(position.market_value) / total_equity * 100) for position in positions),
            default=Decimal("0"),
        ),
    )


def _build_snapshot_constituents(
    *,
    account: Account,
    positions: list[Position],
    aligned_prices: pd.DataFrame,
    portfolio_values: pd.Series,
) -> list[PortfolioConstituentAnalytics]:
    start_portfolio_value = float(portfolio_values.iloc[0])
    constituents: list[PortfolioConstituentAnalytics] = []
    for position in sorted(positions, key=lambda item: item.market_value, reverse=True):
        symbol_prices = aligned_prices[position.symbol]
        contribution_pct = None
        if start_portfolio_value > 0:
            start_value = float(symbol_prices.iloc[0]) * float(position.qty)
            end_value = float(symbol_prices.iloc[-1]) * float(position.qty)
            contribution_pct = _to_decimal(((end_value - start_value) / start_portfolio_value) * 100)
        constituents.append(
            PortfolioConstituentAnalytics(
                symbol=position.symbol,
                quantity=position.qty,
                market_value=position.market_value,
                weight_pct=((position.market_value / account.equity) * 100) if account.equity else Decimal("0"),
                period_return_pct=_calculate_total_return_pct(symbol_prices),
                contribution_pct=contribution_pct,
            )
        )
    return constituents


def _build_transaction_constituents(
    *,
    account: Account,
    positions: list[Position],
    symbols: list[str],
    start_qty: dict[str, Decimal],
    end_qty: dict[str, Decimal],
    trades: list[TradeRecord],
    aligned_prices: pd.DataFrame,
    start_equity: Decimal,
) -> list[PortfolioConstituentAnalytics]:
    position_by_symbol = {position.symbol.upper(): position for position in positions}
    constituents: list[PortfolioConstituentAnalytics] = []
    for symbol in symbols:
        symbol_trades = [trade for trade in trades if trade.symbol.upper() == symbol]
        start_value = start_qty[symbol] * Decimal(str(aligned_prices[symbol].iloc[0]))
        end_value = end_qty[symbol] * Decimal(str(aligned_prices[symbol].iloc[-1]))
        buy_total = sum((trade.total for trade in symbol_trades if trade.is_buy), Decimal("0"))
        net_trade_cash = sum(
            (-trade.total if trade.is_buy else trade.total for trade in symbol_trades),
            Decimal("0"),
        )
        invested_base = abs(start_value) + buy_total
        period_return_pct = None
        if invested_base > 0:
            period_return_pct = _to_decimal(
                float(((end_value + net_trade_cash - start_value) / invested_base) * 100)
            )
        contribution_pct = None
        if start_equity > 0:
            contribution_pct = _to_decimal(
                float(((end_value + net_trade_cash - start_value) / start_equity) * 100)
            )
        current_position = position_by_symbol.get(symbol)
        market_value = current_position.market_value if current_position else end_value
        quantity = current_position.qty if current_position else end_qty[symbol]
        constituents.append(
            PortfolioConstituentAnalytics(
                symbol=symbol,
                quantity=quantity,
                market_value=market_value,
                weight_pct=(market_value / account.equity * 100) if account.equity else Decimal("0"),
                period_return_pct=period_return_pct,
                contribution_pct=contribution_pct,
            )
        )
    return sorted(constituents, key=lambda item: item.market_value, reverse=True)


def _build_result(
    *,
    account: Account,
    positions: list[Position],
    generated_at: datetime,
    history_start: datetime,
    history_end: datetime,
    aligned_prices: pd.DataFrame,
    benchmark_prices: pd.Series,
    data_source: str,
    benchmark_symbol: str,
    methodology: str,
    metrics: _SeriesMetrics,
    exposure: PortfolioExposureSummary,
    constituents: list[PortfolioConstituentAnalytics],
    portfolio_values: pd.Series,
    cash_values: pd.Series,
    positions_values: pd.Series,
    lookback_days: int,
) -> PortfolioAnalyticsResult:
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
        methodology=methodology,
        total_equity=account.equity,
        cash=account.cash,
        position_count=len(positions),
        trading_days=max(len(aligned_prices) - 1, 0),
        cumulative_return_pct=metrics.cumulative_return_pct,
        benchmark_return_pct=metrics.benchmark_return_pct,
        excess_return_pct=metrics.excess_return_pct,
        annualized_volatility_pct=metrics.annualized_volatility_pct,
        benchmark_volatility_pct=metrics.benchmark_volatility_pct,
        sharpe_ratio=metrics.sharpe_ratio,
        benchmark_correlation=metrics.benchmark_correlation,
        max_drawdown_pct=metrics.max_drawdown_pct,
        exposure=exposure,
        rolling_returns=rolling_returns,
        constituents=constituents,
        equity_curve=_build_equity_curve_points(portfolio_values, cash_values, positions_values),
    )


def _build_equity_curve_points(
    portfolio_values: pd.Series,
    cash_values: pd.Series,
    positions_values: pd.Series,
) -> list[EquityCurvePoint]:
    return [
        EquityCurvePoint(
            timestamp=timestamp.to_pydatetime(),
            equity=_to_decimal(float(portfolio_values.loc[timestamp])),
            cash=_to_decimal(float(cash_values.loc[timestamp])),
            positions_value=_to_decimal(float(positions_values.loc[timestamp])),
        )
        for timestamp in portfolio_values.index
    ]


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


def _as_naive(value: datetime) -> datetime:
    """Normalize datetimes for ledger timestamp comparisons."""
    if value.tzinfo is None:
        return value
    return value.replace(tzinfo=None)
