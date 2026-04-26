#!/usr/bin/env python3
"""Generate versioned REST and MCP contract snapshots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kodiak_server.contracts import (
    DEFAULT_CONTRACT_DIR,
    MCP_TOOLS_FILENAME,
    REST_OPENAPI_FILENAME,
    canonical_json,
    generate_contracts,
    generate_mcp_tools_contract,
    generate_rest_openapi_contract,
    load_contract,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_CONTRACT_DIR,
        help=f"Directory for generated artifacts. Defaults to {DEFAULT_CONTRACT_DIR}.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if checked-in contract snapshots do not match generated output.",
    )
    args = parser.parse_args()
    rest_path = args.output_dir / REST_OPENAPI_FILENAME
    mcp_path = args.output_dir / MCP_TOOLS_FILENAME

    if not args.check:
        artifacts = generate_contracts(args.output_dir)
        for path in artifacts:
            print(path)
        return 0

    current = {
        rest_path: generate_rest_openapi_contract(),
        mcp_path: generate_mcp_tools_contract(),
    }
    mismatches = []
    for path, data in current.items():
        if not path.exists() or canonical_json(load_contract(path)) != canonical_json(data):
            mismatches.append(path)
    if mismatches:
        for path in mismatches:
            print(f"Contract snapshot is stale: {path}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
