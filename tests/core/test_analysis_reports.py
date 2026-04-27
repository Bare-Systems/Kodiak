"""Tests for headless analysis report generation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from kodiak.api.broker import OrderSide, OrderStatus
from kodiak.app.reports import (
    build_analysis_report,
    export_analysis_report,
    render_analysis_report,
)
from kodiak.data.ledger import TradeLedger


def _ledger_with_trade_pair(tmp_path: Path) -> TradeLedger:
    ledger = TradeLedger(tmp_path / "trades.db")
    opened_at = datetime.now() - timedelta(days=1, hours=1)
    closed_at = datetime.now() - timedelta(days=1)
    ledger.record_trade(
        order_id="buy-1",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=Decimal("2"),
        price=Decimal("100"),
        status=OrderStatus.FILLED,
        rule_id="trend:entry",
        timestamp=opened_at,
    )
    ledger.record_trade(
        order_id="sell-1",
        symbol="AAPL",
        side=OrderSide.SELL,
        quantity=Decimal("2"),
        price=Decimal("110"),
        status=OrderStatus.FILLED,
        rule_id="trend:exit",
        timestamp=closed_at,
    )
    return ledger


def test_build_analysis_report_is_json_serializable(tmp_path: Path) -> None:
    ledger = _ledger_with_trade_pair(tmp_path)

    report = build_analysis_report(
        ledger=ledger,
        symbol="aapl",
        days=7,
        include_portfolio=False,
    )

    assert report["report_type"] == "analysis"
    assert report["parameters"]["symbol"] == "AAPL"
    assert report["trade_count"] == 2
    assert report["trade_performance"]["summary"]["net_profit"] == "20.00"
    assert report["trade_history"][0]["symbol"] == "AAPL"
    json.dumps(report)


def test_render_analysis_report_markdown(tmp_path: Path) -> None:
    ledger = _ledger_with_trade_pair(tmp_path)
    report = build_analysis_report(ledger=ledger, days=7)

    content = render_analysis_report(report, format="markdown")

    assert content.startswith("# Kodiak Analysis Report")
    assert "## Trade Performance" in content
    assert "| Time | Symbol | Side | Qty | Price | Total | Status |" in content


def test_export_analysis_report_writes_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = _ledger_with_trade_pair(tmp_path)

    monkeypatch.setattr(
        "kodiak.app.reports.TradeLedger",
        lambda: ledger,
    )
    output = tmp_path / "analysis-report.json"

    result = export_analysis_report(output_path=output, days=7)

    assert result["path"] == str(output)
    assert result["content"] is None
    assert output.is_file()
    data = json.loads(output.read_text())
    assert data["trade_count"] == 2
