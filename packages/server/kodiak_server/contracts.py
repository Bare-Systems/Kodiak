"""Contract snapshot generation for Kodiak's public headless interfaces."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

CONTRACT_VERSION = "v1"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT_DIR = PROJECT_ROOT / "contracts"
REST_OPENAPI_FILENAME = f"rest-openapi.{CONTRACT_VERSION}.json"
MCP_TOOLS_FILENAME = f"mcp-tools.{CONTRACT_VERSION}.json"


def canonical_json(data: dict[str, Any]) -> str:
    """Return deterministic JSON for checked-in contract artifacts."""
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def generate_rest_openapi_contract() -> dict[str, Any]:
    """Generate the REST OpenAPI contract snapshot."""
    from kodiak_server.rest.app import create_rest_app

    return create_rest_app().openapi()


async def _generate_mcp_tools_contract_async() -> dict[str, Any]:
    from kodiak.mcp.tools import build_server

    server = build_server()
    tools = await server.list_tools()
    serialized_tools = [
        tool.model_dump(mode="json", exclude_none=True)
        for tool in sorted(tools, key=lambda item: item.name)
    ]
    return {
        "contract_version": CONTRACT_VERSION,
        "server": server.name,
        "tool_count": len(serialized_tools),
        "tools": serialized_tools,
    }


def generate_mcp_tools_contract() -> dict[str, Any]:
    """Generate the MCP tool schema contract snapshot."""
    return asyncio.run(_generate_mcp_tools_contract_async())


def generate_contracts(output_dir: Path = DEFAULT_CONTRACT_DIR) -> dict[Path, dict[str, Any]]:
    """Generate and write all public contract snapshots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        output_dir / REST_OPENAPI_FILENAME: generate_rest_openapi_contract(),
        output_dir / MCP_TOOLS_FILENAME: generate_mcp_tools_contract(),
    }
    for path, data in artifacts.items():
        path.write_text(canonical_json(data), encoding="utf-8")
    return artifacts


def load_contract(path: Path) -> dict[str, Any]:
    """Load a contract artifact from disk."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
