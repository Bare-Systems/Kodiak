"""Standard response envelope for all Kodiak REST API endpoints.

Every successful response:
    {"data": <payload>, "error": null, "meta": {"request_id": "...", "version": "v1"}}

Every error response:
    {"data": null, "error": {"code": "...", "message": "...", ...}, "meta": {...}}

Route handlers call ok() for success. Exception handlers call err() for failures.
The request_id in meta comes from the RequestContext set by the request middleware.
"""

from __future__ import annotations

from typing import Any


def ok(data: Any, request_id: str) -> dict[str, Any]:
    """Wrap a successful response payload in the standard envelope."""
    return {
        "data": data,
        "error": None,
        "meta": {"request_id": request_id, "version": "v1"},
    }


def err(
    code: str,
    message: str,
    request_id: str,
    details: dict[str, Any] | None = None,
    suggestion: str | None = None,
) -> dict[str, Any]:
    """Wrap an error in the standard envelope."""
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    if suggestion:
        error["suggestion"] = suggestion
    return {
        "data": None,
        "error": error,
        "meta": {"request_id": request_id, "version": "v1"},
    }
