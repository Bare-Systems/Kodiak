"""Central audit log for CLI, MCP, and REST actions.

Phase 3 (MCP roadmap): log sensitive operations from both interfaces
so we have an immutable trail for compliance and debugging.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_audit_source: ContextVar[str] = ContextVar("audit_source", default="cli")
_audit_actor: ContextVar[str | None] = ContextVar("audit_actor", default=None)
_audit_request_id: ContextVar[str | None] = ContextVar("audit_request_id", default=None)
_audit_role: ContextVar[str | None] = ContextVar("audit_role", default=None)
_audit_client_ip: ContextVar[str | None] = ContextVar("audit_client_ip", default=None)


def set_audit_source(source: str) -> None:
    """Set the current audit source (e.g. 'cli', 'mcp', 'rest') for this context."""
    _audit_source.set(source)


def get_audit_source() -> str:
    """Return the current audit source."""
    return _audit_source.get()


def set_audit_context(
    *,
    actor: str | None = None,
    request_id: str | None = None,
    role: str | None = None,
    source: str | None = None,
    client_ip: str | None = None,
) -> None:
    """Set actor, request ID, role, source IP, and/or source for the current async context.

    Called by REST middleware on every request so that all log_action calls
    within that request automatically carry identity and tracing fields.
    """
    if actor is not None:
        _audit_actor.set(actor)
    if request_id is not None:
        _audit_request_id.set(request_id)
    if role is not None:
        _audit_role.set(role)
    if source is not None:
        _audit_source.set(source)
    if client_ip is not None:
        _audit_client_ip.set(client_ip)


def clear_audit_context() -> None:
    """Clear audit metadata for the current async context."""
    _audit_actor.set(None)
    _audit_request_id.set(None)
    _audit_role.set(None)
    _audit_client_ip.set(None)


def log_action(
    action: str,
    details: dict[str, Any],
    *,
    error: str | None = None,
    log_dir: Path | None = None,
) -> None:
    """Append one audit record to the audit log.

    Args:
        action: Action name (e.g. 'place_order', 'create_strategy', 'stop_engine').
        details: Structured details (symbol, qty, order_id, etc.). Keep small; no secrets.
        error: If the action failed, a short error message.
        log_dir: Directory for audit.log. If None, no write (caller should pass config.log_dir).
    """
    if log_dir is None:
        return
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "audit.log"
    record: dict[str, Any] = {
        "ts": datetime.now(tz=UTC).isoformat(),
        "source": _audit_source.get(),
        "action": action,
        "details": details,
    }
    actor = _audit_actor.get()
    if actor is not None:
        record["actor"] = actor
    role = _audit_role.get()
    if role is not None:
        record["role"] = role
    request_id = _audit_request_id.get()
    if request_id is not None:
        record["request_id"] = request_id
    client_ip = _audit_client_ip.get()
    if client_ip is not None:
        record["client_ip"] = client_ip
    if error is not None:
        record["error"] = error
    line = json.dumps(record, default=str) + "\n"
    try:
        with open(log_file, "a") as f:
            f.write(line)
    except OSError:
        pass  # Don't fail the request if audit write fails
