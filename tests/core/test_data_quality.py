"""Tests for historical data quality validation."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import pytest
from kodiak.data.providers.base import TimeFrame, validate_ohlcv_frame
from kodiak.data.providers.cached_provider import CachedDataProvider


def _bars(close: float = 100.0) -> pd.DataFrame:
    index = pd.date_range("2024-01-02", periods=1, tz="US/Eastern")
    return pd.DataFrame(
        {
            "open": [close],
            "high": [close],
            "low": [close],
            "close": [close],
            "volume": [1000.0],
        },
        index=index,
    )


def test_validate_ohlcv_frame_rejects_non_finite_values() -> None:
    frame = _bars(float("-inf"))

    with pytest.raises(ValueError, match="non-finite"):
        validate_ohlcv_frame(frame, "SPY", "CSV")


class _Provider:
    def get_bars(
        self,
        symbols: list[str],
        start: datetime,
        end: datetime,
        timeframe: TimeFrame = TimeFrame.DAY_1,
    ) -> dict[str, pd.DataFrame]:
        return {symbol: _bars(101.0) for symbol in symbols}


def test_cached_provider_discards_invalid_cache(tmp_path) -> None:
    provider = CachedDataProvider(_Provider(), cache_dir=tmp_path, ttl_minutes=60)
    start = datetime(2024, 1, 1)
    end = datetime(2024, 1, 31)

    first = provider.get_bars(["SPY"], start, end)
    cache_file = next((tmp_path / "SPY").glob("*.parquet"))
    _bars(float("-inf")).to_parquet(cache_file, index=True)

    second = provider.get_bars(["SPY"], start, end)

    assert first["SPY"]["close"].iloc[0] == 101.0
    assert second["SPY"]["close"].iloc[0] == 101.0
