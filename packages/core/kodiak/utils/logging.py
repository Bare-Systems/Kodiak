"""Logging configuration for Kodiak."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

_request_id_var: ContextVar[str | None] = ContextVar("log_request_id", default=None)
_actor_var: ContextVar[str | None] = ContextVar("log_actor", default=None)
_role_var: ContextVar[str | None] = ContextVar("log_role", default=None)
_client_ip_var: ContextVar[str | None] = ContextVar("log_client_ip", default=None)
_method_var: ContextVar[str | None] = ContextVar("log_method", default=None)
_path_var: ContextVar[str | None] = ContextVar("log_path", default=None)


def set_log_context(
    *,
    request_id: str | None = None,
    actor: str | None = None,
    role: str | None = None,
    client_ip: str | None = None,
    method: str | None = None,
    path: str | None = None,
) -> None:
    """Set async-local log context for the current request/task."""
    _request_id_var.set(request_id)
    _actor_var.set(actor)
    _role_var.set(role)
    _client_ip_var.set(client_ip)
    _method_var.set(method)
    _path_var.set(path)


def clear_log_context() -> None:
    """Clear async-local log context after a request/task completes."""
    set_log_context()


class ContextFilter(logging.Filter):
    """Inject async-local request context into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get()
        record.actor = _actor_var.get()
        record.role = _role_var.get()
        record.client_ip = _client_ip_var.get()
        record.method = _method_var.get()
        record.path = _path_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Render structured JSON logs."""

    extra_fields = (
        "event",
        "request_id",
        "actor",
        "role",
        "client_ip",
        "method",
        "path",
        "status_code",
        "duration_ms",
        "cycle",
        "sleep_time_ms",
        "market_open",
        "strategy_count",
        "action_count",
        "scheduled_enabled_count",
        "dry_run",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self.extra_fields:
            value = getattr(record, field, None)
            if value is not None and value != "":
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    """Emit a structured log event with optional extra fields."""
    logger.log(level, event, extra={"event": event, **fields})


def _build_formatter(log_format: str) -> logging.Formatter:
    if log_format == "json":
        return JsonFormatter()
    return logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _build_file_formatter(log_format: str) -> logging.Formatter:
    if log_format == "json":
        return JsonFormatter()
    return logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def setup_logging(
    log_dir: Path | None = None,
    level: int = logging.INFO,
    log_to_file: bool = True,
    console_stream: TextIO | None = None,
    log_format: str = "text",
) -> logging.Logger:
    """Set up logging for the application.

    Args:
        log_dir: Directory for log files. If None, only console logging.
        level: Logging level.
        log_to_file: Whether to log to file in addition to console.
        console_stream: Stream for console logging. Defaults to sys.stdout.
            Use sys.stderr for MCP stdio transport to avoid corrupting the
            protocol stream.
        log_format: Log rendering format (`text` or `json`).

    Returns:
        Configured logger instance.
    """
    if log_format not in {"text", "json"}:
        raise ValueError("log_format must be 'text' or 'json'")

    stream = console_stream if console_stream is not None else sys.stdout
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)
    console_handler.setFormatter(_build_formatter(log_format))
    console_handler.addFilter(ContextFilter())

    file_handler: logging.Handler | None = None
    trade_handler: logging.Handler | None = None
    if log_to_file and log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "kodiak.log")
        file_handler.setLevel(level)
        file_handler.setFormatter(_build_file_formatter(log_format))
        file_handler.addFilter(ContextFilter())

        trade_handler = logging.FileHandler(log_dir / "trades.log")
        trade_handler.setLevel(logging.INFO)
        trade_handler.setFormatter(_build_file_formatter(log_format))
        trade_handler.addFilter(ContextFilter())

    for logger_name in ("kodiak", "trader", "kodiak_server"):
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.handlers.clear()
        logger.addHandler(console_handler)
        if file_handler is not None:
            logger.addHandler(file_handler)
        logger.propagate = False

    for logger_name in ("kodiak.trades", "trader.trades"):
        trade_logger = logging.getLogger(logger_name)
        trade_logger.handlers.clear()
        trade_logger.setLevel(logging.INFO)
        if trade_handler is not None:
            trade_logger.addHandler(trade_handler)
        trade_logger.propagate = False

    return logging.getLogger("kodiak")


def get_logger(name: str = "kodiak") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
