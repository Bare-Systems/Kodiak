"""Tests for fundamentals ingestion."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

import pytest
from kodiak.data.research import (
    FileFundamentalsProvider,
    ingest_fundamentals,
    load_fundamental_records,
)


def test_ingest_csv_writes_json_map_readable_by_provider(tmp_path) -> None:
    input_path = tmp_path / "input.csv"
    output_dir = tmp_path / "fundamentals"
    input_path.write_text(
        "\n".join(
            [
                "symbol,source,as_of,currency,market_cap,pe_ratio,sector",
                "AAPL,manual,2026-04-24,USD,3000000000000,28.5,Technology",
                "MSFT,manual,2026-04-24,USD,3200000000000,31.1,Technology",
            ]
        )
    )

    result = ingest_fundamentals(input_path, output_dir)
    record = FileFundamentalsProvider(output_dir).get_fundamentals("aapl")

    assert result.count == 2
    assert result.output_files == [output_dir / "fundamentals.json"]
    assert record.symbol == "AAPL"
    assert record.market_cap == Decimal("3000000000000")
    assert record.metadata["sector"] == "Technology"


def test_ingest_json_files_layout(tmp_path) -> None:
    input_path = tmp_path / "input.json"
    output_dir = tmp_path / "fundamentals"
    input_path.write_text(
        json.dumps(
            {
                "NVDA": {
                    "source": "manual",
                    "as_of": "2026-04-24",
                    "currency": "USD",
                    "pe_ratio": "40.2",
                }
            }
        )
    )

    result = ingest_fundamentals(input_path, output_dir, output_format="json-files")

    assert result.output_files == [output_dir / "NVDA.json"]
    assert FileFundamentalsProvider(output_dir).get_fundamentals("NVDA").pe_ratio == Decimal("40.2")


def test_load_fundamental_records_rejects_duplicate_symbols(tmp_path) -> None:
    input_path = tmp_path / "input.csv"
    input_path.write_text(
        "\n".join(
            [
                "symbol,as_of,pe_ratio",
                "AAPL,2026-04-24,28.5",
                "aapl,2026-04-24,29.0",
            ]
        )
    )

    with pytest.raises(ValueError, match="Duplicate"):
        load_fundamental_records(input_path)


def test_ingest_rejects_stale_as_of(tmp_path) -> None:
    input_path = tmp_path / "input.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "symbol": "AAPL",
                    "as_of": "2024-01-01",
                    "pe_ratio": "28.5",
                }
            ]
        )
    )

    with pytest.raises(ValueError, match="stale"):
        ingest_fundamentals(
            input_path,
            tmp_path / "fundamentals",
            max_age_days=30,
            today=date(2026, 4, 24),
        )


def test_ingest_rejects_non_finite_numeric_value(tmp_path) -> None:
    input_path = tmp_path / "input.csv"
    input_path.write_text("symbol,as_of,pe_ratio\nAAPL,2026-04-24,inf\n")

    with pytest.raises(ValueError, match="non-finite"):
        load_fundamental_records(input_path)
