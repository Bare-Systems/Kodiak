"""Tests for structured logging and request tracing."""

from __future__ import annotations

import io
import json
import logging

from kodiak.core.engine import TradingEngine
from kodiak.utils.logging import (
    clear_log_context,
    get_logger,
    log_event,
    set_log_context,
    setup_logging,
)

from tests.core.mocks import MockBroker


def test_log_event_emits_json_with_request_context() -> None:
    stream = io.StringIO()
    setup_logging(log_to_file=False, console_stream=stream, log_format="json")
    logger = get_logger("kodiak_server.rest")

    set_log_context(
        request_id="req-123",
        actor="joe@example.com",
        role="operator",
        client_ip="127.0.0.1",
        method="GET",
        path="/api/v1/strategies/",
    )
    try:
        log_event(logger, logging.INFO, "http_request_complete", status_code=200, duration_ms=12.34)
    finally:
        clear_log_context()

    payload = json.loads(stream.getvalue().strip())
    assert payload["event"] == "http_request_complete"
    assert payload["request_id"] == "req-123"
    assert payload["actor"] == "joe@example.com"
    assert payload["role"] == "operator"
    assert payload["client_ip"] == "127.0.0.1"
    assert payload["method"] == "GET"
    assert payload["path"] == "/api/v1/strategies/"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 12.34


def test_run_once_logs_engine_cycle_metrics_when_market_closed(monkeypatch) -> None:
    stream = io.StringIO()
    setup_logging(log_to_file=False, console_stream=stream, log_format="json")

    monkeypatch.setattr("kodiak.strategies.loader.load_strategies", lambda: [])

    broker = MockBroker()
    broker.set_market_open(False)
    engine = TradingEngine(broker=broker, poll_interval=60, dry_run=True)

    strategy_ids = engine.run_once()

    assert strategy_ids == []
    records = [
        json.loads(line)
        for line in stream.getvalue().splitlines()
        if line.strip()
    ]
    cycle_record = next(record for record in records if record.get("event") == "engine_cycle_complete")
    assert cycle_record["market_open"] is False
    assert cycle_record["action_count"] == 0
    assert cycle_record["strategy_count"] == 0
    assert cycle_record["scheduled_enabled_count"] == 0
    assert cycle_record["sleep_time_ms"] == 0.0
    assert cycle_record["dry_run"] is True
