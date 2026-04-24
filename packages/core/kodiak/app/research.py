"""Research data service functions."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from kodiak.backtest.data import load_data_for_backtest
from kodiak.data.providers.base import TimeFrame
from kodiak.data.research import FileFundamentalsProvider
from kodiak.errors import ValidationError
from kodiak.schemas.research import (
    BenchmarkBarResponse,
    BenchmarkHistoryResponse,
    FundamentalsResponse,
)
from kodiak.utils.config import Config

_EASTERN_TZ = ZoneInfo("America/New_York")


def get_fundamentals(config: Config, symbol: str) -> FundamentalsResponse:
    """Get file-backed fundamentals for a symbol."""
    symbol = symbol.upper()
    data_dir = Path(os.getenv("FUNDAMENTALS_DATA_DIR", str(config.data_dir / "fundamentals")))
    provider = FileFundamentalsProvider(data_dir)
    try:
        record = provider.get_fundamentals(symbol)
    except FileNotFoundError as exc:
        raise ValidationError(
            message=f"Fundamentals are unavailable for {symbol}.",
            code="FUNDAMENTALS_DATA_UNAVAILABLE",
            details={"symbol": symbol, "data_dir": str(data_dir), "reason": str(exc)},
            suggestion=(
                "Set FUNDAMENTALS_DATA_DIR or add a fundamentals.json, fundamentals.csv, "
                "or per-symbol JSON file such as AAPL.json."
            ),
        ) from exc
    except ValueError as exc:
        raise ValidationError(
            message=f"Fundamentals data is invalid for {symbol}.",
            code="FUNDAMENTALS_DATA_INVALID",
            details={"symbol": symbol, "data_dir": str(data_dir), "reason": str(exc)},
        ) from exc
    return FundamentalsResponse.from_domain(record)


def get_benchmark_history(
    config: Config,
    symbol: str,
    start: date,
    end: date,
    data_source: str | None = None,
    timeframe: TimeFrame = TimeFrame.DAY_1,
) -> BenchmarkHistoryResponse:
    """Get normalized historical bars and return stats for a benchmark symbol."""
    symbol = symbol.upper()
    if start > end:
        raise ValidationError(
            message="start must be on or before end",
            details={"start": start.isoformat(), "end": end.isoformat()},
        )

    source = data_source or config.data.source
    start_dt = datetime.combine(start, time.min, tzinfo=_EASTERN_TZ)
    end_dt = datetime.combine(end, time.max, tzinfo=_EASTERN_TZ)

    try:
        history = load_data_for_backtest(
            symbols=[symbol],
            start_date=start_dt,
            end_date=end_dt,
            data_source=source,
            data_dir=config.data.csv_dir,
            timeframe=timeframe,
            config=config,
        )
    except (FileNotFoundError, ValueError, ConnectionError) as exc:
        raise ValidationError(
            message=f"Benchmark history is unavailable for {symbol}.",
            code="BENCHMARK_HISTORY_UNAVAILABLE",
            details={
                "symbol": symbol,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "data_source": source,
                "reason": str(exc),
            },
            suggestion="Provide historical data via HISTORICAL_DATA_DIR or use an available data_source.",
        ) from exc

    bars = history[symbol]
    if bars.empty:
        raise ValidationError(
            message=f"Benchmark history is empty for {symbol}.",
            code="BENCHMARK_HISTORY_EMPTY",
            details={"symbol": symbol, "start": start.isoformat(), "end": end.isoformat()},
        )

    try:
        first_close = _decimal(bars["close"].iloc[0])
        latest_close = _decimal(bars["close"].iloc[-1])
        return_pct = Decimal("0")
        if first_close != 0:
            return_pct = ((latest_close / first_close) - Decimal("1")) * Decimal("100")

        response_bars = [
            BenchmarkBarResponse(
                timestamp=index.isoformat(),
                open=_decimal(row["open"]),
                high=_decimal(row["high"]),
                low=_decimal(row["low"]),
                close=_decimal(row["close"]),
                volume=_decimal(row["volume"]),
            )
            for index, row in bars.iterrows()
        ]
    except ValueError as exc:
        raise ValidationError(
            message=f"Benchmark history contains invalid numeric data for {symbol}.",
            code="BENCHMARK_HISTORY_INVALID",
            details={"symbol": symbol, "data_source": source, "reason": str(exc)},
        ) from exc

    return BenchmarkHistoryResponse(
        generated_at=datetime.now(tz=UTC).isoformat(),
        symbol=symbol,
        data_source=source,
        timeframe=timeframe.value,
        start=bars.index[0].isoformat(),
        end=bars.index[-1].isoformat(),
        bar_count=len(bars),
        first_close=first_close,
        latest_close=latest_close,
        return_pct=return_pct,
        bars=response_bars,
    )


def _decimal(value: Any) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError(f"Non-finite numeric value: {value}")
    return result
