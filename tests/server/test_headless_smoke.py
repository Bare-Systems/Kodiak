"""Tests for the headless smoke harness."""

from __future__ import annotations

from kodiak_server.smoke import run_headless_smoke


def test_headless_smoke_harness_passes() -> None:
    report = run_headless_smoke()

    assert report.ok
    assert {check.name for check in report.checks} == {
        "health",
        "landing_page",
        "rest_auth",
        "rest_schema",
        "rest_envelope",
        "mcp_auth",
        "mcp_tools",
    }
