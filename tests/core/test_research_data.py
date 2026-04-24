"""Tests for research data services."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from kodiak.app.research import get_benchmark_history, get_fundamentals
from kodiak.utils.config import load_config


def test_get_fundamentals_from_symbol_json(tmp_path, monkeypatch) -> None:
    fundamentals_dir = tmp_path / "fundamentals"
    fundamentals_dir.mkdir()
    (fundamentals_dir / "AAPL.json").write_text(
        json.dumps(
            {
                "source": "fixture",
                "as_of": "2026-04-24",
                "currency": "USD",
                "market_cap": "3000000000000",
                "pe_ratio": "28.5",
                "beta": "1.2",
                "sector": "Technology",
            }
        )
    )
    monkeypatch.setenv("FUNDAMENTALS_DATA_DIR", str(fundamentals_dir))

    response = get_fundamentals(load_config(), "aapl")

    assert response.symbol == "AAPL"
    assert response.source == "fixture"
    assert response.market_cap == Decimal("3000000000000")
    assert response.pe_ratio == Decimal("28.5")
    assert response.metadata["sector"] == "Technology"


def test_get_benchmark_history_from_csv(tmp_path, monkeypatch) -> None:
    historical_dir = tmp_path / "historical"
    historical_dir.mkdir()
    (historical_dir / "SPY.csv").write_text(
        "\n".join(
            [
                "timestamp,open,high,low,close,volume",
                "2024-01-02 00:00:00,400,405,399,402,1000000",
                "2024-01-03 00:00:00,402,408,401,406,1100000",
                "2024-01-04 00:00:00,406,410,405,410,1200000",
            ]
        )
    )
    monkeypatch.setenv("HISTORICAL_DATA_DIR", str(historical_dir))

    response = get_benchmark_history(
        load_config(),
        "spy",
        start=date(2024, 1, 2),
        end=date(2024, 1, 4),
    )

    assert response.symbol == "SPY"
    assert response.data_source == "csv"
    assert response.bar_count == 3
    assert response.first_close == Decimal("402.0")
    assert response.latest_close == Decimal("410.0")
    assert response.return_pct > Decimal("0")
    assert len(response.bars) == 3
