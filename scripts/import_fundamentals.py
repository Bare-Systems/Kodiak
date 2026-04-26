#!/usr/bin/env python3
"""Import fundamentals into Kodiak's file-backed research data store."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kodiak.data.research import ingest_fundamentals
from kodiak.utils.config import load_config


def main(argv: list[str] | None = None) -> int:
    """Run the fundamentals importer."""
    parser = argparse.ArgumentParser(
        description="Validate and import fundamentals from CSV or JSON into Kodiak."
    )
    parser.add_argument("input", type=Path, help="Input .csv or .json fundamentals file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to data/fundamentals for the active Kodiak config.",
    )
    parser.add_argument(
        "--format",
        choices=("json-map", "json-files", "csv"),
        default="json-map",
        help="Output layout supported by get_fundamentals (default: json-map).",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=None,
        help="Reject records whose as_of date is older than this many days.",
    )
    args = parser.parse_args(argv)

    config = load_config()
    output_dir = args.output_dir or config.data_dir / "fundamentals"

    try:
        result = ingest_fundamentals(
            input_path=args.input,
            output_dir=output_dir,
            output_format=args.format,
            max_age_days=args.max_age_days,
        )
    except Exception as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1

    print(f"Imported {result.count} fundamentals record(s)")
    for output_file in result.output_files:
        print(output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
