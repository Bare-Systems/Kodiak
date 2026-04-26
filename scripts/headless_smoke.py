#!/usr/bin/env python3
"""Run Kodiak headless release smoke checks."""

from __future__ import annotations

import argparse
import json

from kodiak_server.smoke import run_headless_smoke


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-token",
        default="kodiak-smoke-token",
        help="Temporary bearer token used for in-process authenticated checks.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args()

    report = run_headless_smoke(api_token=args.api_token)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for check in report.checks:
            status = "PASS" if check.ok else "FAIL"
            print(f"{status} {check.name}: {check.detail}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
