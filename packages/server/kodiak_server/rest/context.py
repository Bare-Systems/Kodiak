"""Request context — request ID, actor, and role for each REST request.

A middleware in rest/app.py sets these context vars at the start of every
request so they are available to route handlers, dependencies, and exception
handlers without needing to thread them as explicit parameters everywhere.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass

from fastapi import Request

_request_id_var: ContextVar[str] = ContextVar("request_id", default="")
_actor_var: ContextVar[str | None] = ContextVar("actor", default=None)
_role_var: ContextVar[str | None] = ContextVar("role", default=None)


def set_request_context(
    request_id: str,
    actor: str | None,
    role: str | None,
) -> None:
    """Store request identity in async-local context vars.

    Called once per request by the context middleware before the handler runs.
    """
    _request_id_var.set(request_id)
    _actor_var.set(actor)
    _role_var.set(role)


def get_current_request_id() -> str:
    """Return the current request ID, or a fresh UUID if none is set."""
    return _request_id_var.get() or str(uuid.uuid4())


@dataclass
class RequestContext:
    """Per-request identity fields injected as a FastAPI dependency."""

    request_id: str
    actor: str | None
    role: str | None


def get_request_context(request: Request) -> RequestContext:  # noqa: ARG001
    """FastAPI dependency — returns the context set by the request middleware."""
    return RequestContext(
        request_id=_request_id_var.get(),
        actor=_actor_var.get(),
        role=_role_var.get(),
    )
