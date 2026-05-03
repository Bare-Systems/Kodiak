"""Backtest orchestration service functions."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from kodiak.audit import log_action as audit_log
from kodiak.errors import NotFoundError, ValidationError
from kodiak.schemas.backtests import BacktestRequest, BacktestResponse, BacktestSummary
from kodiak.utils.config import Config


def run_backtest(config: Config, request: BacktestRequest) -> BacktestResponse:
    """Run a backtest for a strategy.

    Args:
        config: Application configuration.
        request: Backtest request schema.

    Returns:
        Backtest response schema.

    Raises:
        ValidationError: If parameters are invalid.
        NotFoundError: If data files not found.
    """
    from kodiak.backtest import (
        BacktestEngine,
        HistoricalBroker,
        load_data_for_backtest,
        save_backtest,
    )

    # Parse dates
    try:
        start_date = datetime.strptime(request.start, "%Y-%m-%d").replace(tzinfo=ZoneInfo("US/Eastern"))
        end_date = datetime.strptime(request.end, "%Y-%m-%d").replace(tzinfo=ZoneInfo("US/Eastern"))
    except ValueError as e:
        raise ValidationError(
            message=f"Invalid date format: {e}",
            code="INVALID_DATE_FORMAT",
            suggestion="Use YYYY-MM-DD format",
        )

    # Validate strategy-specific params
    if request.strategy_type == "trailing-stop":
        if request.trailing_pct is None:
            raise ValidationError(
                message="--trailing-pct is required for trailing-stop strategy",
                code="MISSING_PARAM",
                details={"param": "trailing_pct"},
            )
        strategy_config = {
            "symbol": request.symbol,
            "strategy_type": "trailing_stop",
            "quantity": request.qty,
            "trailing_stop_pct": str(request.trailing_pct),
        }
    elif request.strategy_type == "bracket":
        if request.take_profit is None or request.stop_loss is None:
            raise ValidationError(
                message="--take-profit and --stop-loss are required for bracket strategy",
                code="MISSING_PARAM",
                details={"params": ["take_profit", "stop_loss"]},
            )
        strategy_config = {
            "symbol": request.symbol,
            "strategy_type": "bracket",
            "quantity": request.qty,
            "take_profit_pct": str(request.take_profit),
            "stop_loss_pct": str(request.stop_loss),
        }
    else:
        raise ValidationError(
            message=f"Strategy type {request.strategy_type} not supported for backtesting",
            code="UNSUPPORTED_STRATEGY",
        )

    # Load historical data
    if request.data_dir:
        data_dir_path = Path(request.data_dir)
    else:
        data_dir_path = Path.cwd() / "data" / "historical"

    try:
        historical_data = load_data_for_backtest(
            symbols=[request.symbol],
            start_date=start_date,
            end_date=end_date,
            data_source=request.data_source,
            data_dir=data_dir_path,
        )
    except FileNotFoundError as e:
        default_dir = Path.home() / ".kodiak" / "data" / "historical"
        suggestion = (
            f"CSV file not found: {data_dir_path}/{request.symbol}.csv. "
            f"Set HISTORICAL_DATA_DIR environment variable or create CSV files. "
            f"Default location: {default_dir}. "
            f"See README.md 'Backtesting with CSV Data' section for setup instructions."
        )
        raise NotFoundError(
            message=str(e),
            code="DATA_NOT_FOUND",
            suggestion=suggestion,
        )

    # Create broker and engine
    from kodiak.schemas.backtests import ExecutionConfig
    execution_config = request.execution or ExecutionConfig()

    broker = HistoricalBroker(
        historical_data=historical_data,
        initial_cash=Decimal(str(request.initial_capital)),
        execution_config=execution_config,
    )

    engine = BacktestEngine(
        broker=broker,
        strategy_config=strategy_config,
        start_date=start_date,
        end_date=end_date,
    )

    # Run backtest
    result = engine.run()

    # Save if requested
    if request.save:
        save_backtest(result)

    audit_log(
        "run_backtest",
        {
            "strategy_type": request.strategy_type,
            "symbol": request.symbol,
            "start": request.start,
            "end": request.end,
            "backtest_id": result.id,
            "execution_config": execution_config.model_dump(),
        },
        log_dir=config.log_dir,
    )
    return BacktestResponse.from_domain(result)


def list_backtests_app(data_dir: str | None = None) -> list[BacktestSummary]:
    """List all saved backtests.

    Args:
        data_dir: Data directory path (or None for default).

    Returns:
        List of backtest summary schemas.
    """
    from kodiak.backtest import list_backtests

    data_dir_path = Path(data_dir) if data_dir else None
    backtests = list_backtests(data_dir=data_dir_path)

    return _enrich_backtest_summaries(backtests, data_dir=data_dir_path)


def show_backtest(backtest_id: str, data_dir: str | None = None) -> BacktestResponse:
    """Load and return a backtest result.

    Args:
        backtest_id: Backtest ID.
        data_dir: Data directory path (or None for default).

    Returns:
        Backtest response schema.

    Raises:
        NotFoundError: If backtest not found.
    """
    from kodiak.backtest import load_backtest

    data_dir_path = Path(data_dir) if data_dir else None

    try:
        result = load_backtest(backtest_id, data_dir=data_dir_path)
    except FileNotFoundError:
        raise NotFoundError(
            message=f"Backtest {backtest_id} not found",
            code="BACKTEST_NOT_FOUND",
        )

    return BacktestResponse.from_domain(result)


def compare_backtests(
    backtest_ids: list[str],
    data_dir: str | None = None,
) -> list[BacktestResponse]:
    """Load multiple backtests for comparison.

    Args:
        backtest_ids: List of backtest IDs.
        data_dir: Data directory path (or None for default).

    Returns:
        List of backtest response schemas (skips not-found).
    """
    from kodiak.backtest import load_backtest

    data_dir_path = Path(data_dir) if data_dir else None
    results = []

    for bt_id in backtest_ids:
        try:
            result = load_backtest(bt_id, data_dir=data_dir_path)
            results.append(BacktestResponse.from_domain(result))
        except FileNotFoundError:
            continue  # Skip missing backtests

    return results


def delete_backtest_app(backtest_id: str, data_dir: str | None = None) -> dict[str, str]:
    """Delete a backtest result.

    Args:
        backtest_id: Backtest ID to delete.
        data_dir: Data directory path (or None for default).

    Returns:
        Dict with status message.

    Raises:
        NotFoundError: If backtest not found.
    """
    from kodiak.backtest import delete_backtest

    data_dir_path = Path(data_dir) if data_dir else None

    if not delete_backtest(backtest_id, data_dir=data_dir_path):
        raise NotFoundError(
            message=f"Backtest {backtest_id} not found",
            code="BACKTEST_NOT_FOUND",
        )

    return {"status": "deleted", "backtest_id": backtest_id}


def _enrich_backtest_summaries(
    backtests: list[dict],
    *,
    data_dir: Path | None,
) -> list[BacktestSummary]:
    from kodiak.backtest import load_backtest

    grouped_indexes: dict[str, list[int]] = defaultdict(list)
    summaries: list[BacktestSummary] = []

    for index, entry in enumerate(backtests):
        enriched = dict(entry)
        try:
            result = load_backtest(entry["id"], data_dir=data_dir)
            signature = _strategy_signature(result.strategy_type, result.symbol, result.strategy_config)
            enriched["strategy_signature"] = signature
            enriched["position_state"] = _position_state(result.trades)
            grouped_indexes[signature].append(index)
        except FileNotFoundError:
            enriched["position_state"] = "unknown"
        summaries.append(BacktestSummary.from_index_entry(enriched))

    for indexes in grouped_indexes.values():
        group_size = len(indexes)
        for rank, summary_index in enumerate(indexes, start=1):
            summaries[summary_index].duplicate_group_size = group_size
            summaries[summary_index].duplicate_rank = rank

    return summaries


def _strategy_signature(
    strategy_type: str,
    symbol: str,
    strategy_config: dict[str, object],
) -> str:
    normalized = {
        key: value
        for key, value in strategy_config.items()
        if key
        not in {
            "id",
            "phase",
            "entry_order_id",
            "entry_fill_price",
            "high_watermark",
            "exit_order_ids",
            "scale_state",
            "grid_state",
            "created_at",
            "updated_at",
            "notes",
        }
    }
    payload = json.dumps(
        {
            "strategy_type": strategy_type,
            "symbol": symbol,
            "config": normalized,
        },
        sort_keys=True,
        default=str,
    )
    return f"{strategy_type}:{symbol}:{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:12]}"


def _position_state(trades: list[dict[str, object]]) -> str:
    if not trades:
        return "flat"

    buy_qty = Decimal("0")
    sell_qty = Decimal("0")
    for trade in trades:
        qty = Decimal(str(trade.get("qty", "0")))
        side = str(trade.get("side", "")).lower()
        if side == "buy":
            buy_qty += qty
        elif side == "sell":
            sell_qty += qty

    if buy_qty > sell_qty:
        return "open"
    if sell_qty > buy_qty:
        return "short_or_inconsistent"
    return "flat"
