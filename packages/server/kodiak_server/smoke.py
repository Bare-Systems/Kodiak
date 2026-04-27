"""Headless smoke checks for Kodiak Server release validation."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SmokeCheck:
    """Result for one smoke check."""

    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class SmokeReport:
    """Aggregated headless smoke result."""

    checks: list[SmokeCheck]

    @property
    def ok(self) -> bool:
        """True when every smoke check passed."""
        return all(check.ok for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the smoke report for CLI or CI output."""
        return {
            "ok": self.ok,
            "checks": [
                {"name": check.name, "ok": check.ok, "detail": check.detail}
                for check in self.checks
            ],
        }


@contextmanager
def _temporary_env(values: dict[str, str]) -> Iterator[None]:
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def _disable_logging() -> Iterator[None]:
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(previous)


def _pass(name: str, detail: str) -> SmokeCheck:
    return SmokeCheck(name=name, ok=True, detail=detail)


def _fail(name: str, detail: str) -> SmokeCheck:
    return SmokeCheck(name=name, ok=False, detail=detail)


def run_headless_smoke(api_token: str = "kodiak-smoke-token") -> SmokeReport:
    """Run in-process smoke checks for the headless server and MCP registry.

    The harness avoids live broker execution and network sockets. It creates the
    ASGI app in-process, validates authenticated REST behavior through
    TestClient, and validates MCP availability through the registered FastMCP
    tool list.
    """
    checks: list[SmokeCheck] = []
    headers = {"Authorization": f"Bearer {api_token}"}

    with (
        _temporary_env({"KODIAK_API_TOKEN": api_token, "KODIAK_LOG_TO_FILE": "false"}),
        _disable_logging(),
    ):
        from fastapi.testclient import TestClient
        from kodiak.mcp.tools import build_server

        from kodiak_server.main import create_app

        client = TestClient(create_app(), raise_server_exceptions=False)

        response = client.get("/health")
        if response.status_code == 200 and response.json().get("status") == "ok":
            checks.append(_pass("health", "GET /health returned status=ok"))
        else:
            checks.append(_fail("health", f"GET /health returned {response.status_code}"))

        response = client.get("/")
        if (
            response.status_code == 200
            and "Kodiak Headless Server" in response.text
            and "KODIAK_API_TOKEN" not in response.text
        ):
            checks.append(_pass("landing_page", "GET / served the minimal headless page"))
        else:
            checks.append(_fail("landing_page", f"GET / returned {response.status_code}"))

        response = client.get("/api/v1/schema.json")
        if response.status_code == 401:
            checks.append(_pass("rest_auth", "REST schema rejects missing bearer token"))
        else:
            checks.append(_fail("rest_auth", f"Unauthenticated schema returned {response.status_code}"))

        response = client.get("/api/v1/schema.json", headers=headers)
        schema = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        paths = schema.get("paths", {}) if isinstance(schema, dict) else {}
        if response.status_code == 200 and "/v1/engine/status" in paths:
            checks.append(_pass("rest_schema", f"REST OpenAPI returned {len(paths)} paths"))
        else:
            checks.append(_fail("rest_schema", f"Authenticated schema returned {response.status_code}"))

        response = client.get("/api/v1/engine/status", headers=headers)
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        if (
            response.status_code in {200, 400}
            and isinstance(body, dict)
            and "data" in body
            and "error" in body
            and "meta" in body
        ):
            checks.append(_pass("rest_envelope", "Engine status returned the REST envelope"))
        else:
            checks.append(_fail("rest_envelope", f"Engine status returned {response.status_code}"))

        response = client.get("/mcp/")
        if response.status_code == 401:
            checks.append(_pass("mcp_auth", "MCP endpoint rejects missing bearer token"))
        else:
            checks.append(_fail("mcp_auth", f"Unauthenticated MCP returned {response.status_code}"))

        server = build_server()
        tools = asyncio.run(server.list_tools())
        tool_names = {tool.name for tool in tools}
        required_tools = {
            "get_status",
            "get_portfolio_analytics",
            "get_rebalance_plan",
            "export_analysis_report",
            "stop_engine",
        }
        missing = sorted(required_tools - tool_names)
        if len(tools) >= 39 and not missing:
            checks.append(_pass("mcp_tools", f"MCP registered {len(tools)} tools"))
        else:
            detail = f"MCP registered {len(tools)} tools"
            if missing:
                detail = f"{detail}; missing {', '.join(missing)}"
            checks.append(_fail("mcp_tools", detail))

    return SmokeReport(checks=checks)
