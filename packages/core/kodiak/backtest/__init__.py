"""Backtesting module for Kodiak.

This module provides backtesting capabilities to test trading strategies
against historical data before risking real capital.
"""

from kodiak.backtest.broker import HistoricalBroker
from kodiak.backtest.data import load_csv_data, load_data_for_backtest
from kodiak.backtest.engine import BacktestEngine
from kodiak.backtest.results import BacktestResult
from kodiak.backtest.store import (
    delete_backtest,
    list_backtests,
    load_backtest,
    save_backtest,
)

__all__ = [
    "HistoricalBroker",
    "load_csv_data",
    "load_data_for_backtest",
    "BacktestEngine",
    "BacktestResult",
    "save_backtest",
    "load_backtest",
    "list_backtests",
    "delete_backtest",
]
