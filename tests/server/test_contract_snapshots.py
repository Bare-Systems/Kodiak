"""Snapshot tests for Kodiak's public REST and MCP contracts."""

from __future__ import annotations

from kodiak_server.contracts import (
    DEFAULT_CONTRACT_DIR,
    MCP_TOOLS_FILENAME,
    REST_OPENAPI_FILENAME,
    generate_mcp_tools_contract,
    generate_rest_openapi_contract,
    load_contract,
)


def test_rest_openapi_contract_snapshot_is_current() -> None:
    expected = load_contract(DEFAULT_CONTRACT_DIR / REST_OPENAPI_FILENAME)
    current = generate_rest_openapi_contract()

    assert current == expected


def test_mcp_tools_contract_snapshot_is_current() -> None:
    expected = load_contract(DEFAULT_CONTRACT_DIR / MCP_TOOLS_FILENAME)
    current = generate_mcp_tools_contract()

    assert current == expected
