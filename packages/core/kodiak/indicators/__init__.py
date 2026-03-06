"""Indicators library."""

from __future__ import annotations

from typing import Any

from kodiak.indicators.base import IndicatorSpec
from kodiak.indicators.custom import RollingHighLow
from kodiak.indicators.momentum import MACD, RSI
from kodiak.indicators.trend import EMA, SMA
from kodiak.indicators.volatility import ATR, BollingerBands
from kodiak.indicators.volume import OBV, VWAP

INDICATORS = {
    "sma": SMA,
    "ema": EMA,
    "rsi": RSI,
    "macd": MACD,
    "atr": ATR,
    "bbands": BollingerBands,
    "obv": OBV,
    "vwap": VWAP,
    "rolling_high_low": RollingHighLow,
}


def list_indicators() -> list[IndicatorSpec]:
    """Return specs for all available indicators."""
    return [cls().spec for cls in INDICATORS.values()]


def get_indicator(name: str, **params: Any):
    """Instantiate indicator by name."""
    if name not in INDICATORS:
        raise ValueError(f"Unknown indicator: {name}")
    return INDICATORS[name](**params)


__all__ = [
    "IndicatorSpec",
    "list_indicators",
    "get_indicator",
    "INDICATORS",
    "SMA",
    "EMA",
    "RSI",
    "MACD",
    "ATR",
    "BollingerBands",
    "OBV",
    "VWAP",
    "RollingHighLow",
]
