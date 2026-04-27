"""Headless analysis report generation."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from kodiak.data.ledger import TradeLedger, TradeRecord
from kodiak.errors import AppError, ValidationError
from kodiak.utils.config import Config

ReportFormat = Literal["json", "markdown"]


def build_analysis_report(
    config: Config | None = None,
    *,
    symbol: str | None = None,
    days: int = 30,
    limit: int = 1000,
    include_portfolio: bool = False,
    portfolio_lookback_days: int = 252,
    benchmark_symbol: str = "SPY",
    ledger: TradeLedger | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable analysis report.

    The report intentionally remains data-only so it can be consumed by CLI,
    REST, MCP, schedulers, or any other headless integration.
    """
    _validate_report_inputs(
        days=days,
        limit=limit,
        portfolio_lookback_days=portfolio_lookback_days,
    )

    normalized_symbol = symbol.upper() if symbol else None
    trade_ledger = ledger or TradeLedger()
    since = datetime.now() - timedelta(days=days)
    trades = trade_ledger.get_trades(
        symbol=normalized_symbol,
        since=since,
        limit=limit,
    )

    report: dict[str, Any] = {
        "report_type": "analysis",
        "generated_at": datetime.now(UTC).isoformat(),
        "parameters": {
            "symbol": normalized_symbol,
            "days": days,
            "limit": limit,
            "include_portfolio": include_portfolio,
            "portfolio_lookback_days": portfolio_lookback_days,
            "benchmark_symbol": benchmark_symbol.upper(),
        },
        "trade_count": len(trades),
        "today_pnl": _today_pnl_payload(trade_ledger, normalized_symbol),
        "trade_performance": _trade_performance_payload(trades),
        "trade_history": [_trade_record_payload(trade) for trade in trades],
    }

    if include_portfolio:
        report["portfolio_analytics"] = _portfolio_payload(
            config,
            lookback_days=portfolio_lookback_days,
            benchmark_symbol=benchmark_symbol,
        )

    return report


def render_analysis_report(
    report: dict[str, Any],
    *,
    format: ReportFormat,
) -> str:
    """Render an analysis report as JSON or Markdown."""
    if format == "json":
        return json.dumps(report, indent=2, default=str)
    if format == "markdown":
        return _render_markdown(report)
    raise ValidationError(
        f"Unsupported report format: {format}",
        details={"format": format, "supported": ["json", "markdown"]},
    )


def export_analysis_report(
    config: Config | None = None,
    *,
    output_path: Path | str | None = None,
    format: ReportFormat = "json",
    symbol: str | None = None,
    days: int = 30,
    limit: int = 1000,
    include_portfolio: bool = False,
    portfolio_lookback_days: int = 252,
    benchmark_symbol: str = "SPY",
) -> dict[str, Any]:
    """Generate and optionally write a headless analysis report."""
    report = build_analysis_report(
        config,
        symbol=symbol,
        days=days,
        limit=limit,
        include_portfolio=include_portfolio,
        portfolio_lookback_days=portfolio_lookback_days,
        benchmark_symbol=benchmark_symbol,
    )
    content = render_analysis_report(report, format=format)

    result: dict[str, Any] = {
        "format": format,
        "bytes": len(content.encode("utf-8")),
        "path": None,
        "report": report if format == "json" else None,
        "content": content if output_path is None else None,
    }

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        result["path"] = str(path)
        result["content"] = None

    return result


def _validate_report_inputs(
    *,
    days: int,
    limit: int,
    portfolio_lookback_days: int,
) -> None:
    if days < 1:
        raise ValidationError("days must be at least 1", details={"days": days})
    if limit < 1:
        raise ValidationError("limit must be at least 1", details={"limit": limit})
    if portfolio_lookback_days < 1:
        raise ValidationError(
            "portfolio_lookback_days must be at least 1",
            details={"portfolio_lookback_days": portfolio_lookback_days},
        )


def _trade_performance_payload(trades: list[TradeRecord]) -> dict[str, Any] | None:
    if not trades:
        return None

    from kodiak.analysis.trades import analyze_trades
    from kodiak.schemas.analysis import AnalysisResponse

    return AnalysisResponse.from_domain(analyze_trades(trades)).model_dump(mode="json")


def _trade_record_payload(trade: TradeRecord) -> dict[str, Any]:
    return {
        "id": trade.id,
        "order_id": trade.order_id,
        "symbol": trade.symbol,
        "side": trade.side,
        "quantity": str(trade.quantity),
        "price": str(trade.price),
        "total": str(trade.total),
        "status": trade.status,
        "rule_id": trade.rule_id,
        "timestamp": trade.timestamp.isoformat(),
    }


def _today_pnl_payload(ledger: TradeLedger, symbol: str | None) -> str:
    if symbol is None:
        return str(ledger.get_total_today_pnl())
    return str(ledger.get_today_pnl().get(symbol, 0))


def _portfolio_payload(
    config: Config | None,
    *,
    lookback_days: int,
    benchmark_symbol: str,
) -> dict[str, Any]:
    if config is None:
        return {
            "available": False,
            "error": "CONFIGURATION_REQUIRED",
            "message": "Portfolio analytics require a loaded Kodiak config.",
        }

    from kodiak.app.portfolio import get_portfolio_analytics

    try:
        result = get_portfolio_analytics(
            config,
            lookback_days=lookback_days,
            benchmark_symbol=benchmark_symbol.upper(),
        )
        return {"available": True, "data": result.model_dump(mode="json")}
    except AppError as exc:
        return {
            "available": False,
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
            "suggestion": exc.suggestion,
        }


def _render_markdown(report: dict[str, Any]) -> str:
    params = report["parameters"]
    lines = [
        "# Kodiak Analysis Report",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Symbol: {params['symbol'] or 'ALL'}",
        f"- Lookback: {params['days']} days",
        f"- Trades: {report['trade_count']}",
        f"- Today's realized P/L: ${report['today_pnl']}",
        "",
    ]

    performance = report.get("trade_performance")
    if performance:
        summary = performance["summary"]
        lines.extend(
            [
                "## Trade Performance",
                "",
                f"- Win rate: {summary['win_rate']}%",
                f"- Net P/L: ${summary['net_profit']}",
                f"- Gross profit: ${summary['gross_profit']}",
                f"- Gross loss: ${summary['gross_loss']}",
                f"- Profit factor: {summary['profit_factor']}",
                "",
            ]
        )
    else:
        lines.extend(["## Trade Performance", "", "No trades found for the selected window.", ""])

    portfolio = report.get("portfolio_analytics")
    if portfolio:
        lines.extend(["## Portfolio Analytics", ""])
        if portfolio.get("available"):
            data = portfolio["data"]
            lines.extend(
                [
                    f"- Benchmark: {data['benchmark_symbol']}",
                    f"- Return: {data['total_return_pct']}%",
                    f"- Benchmark return: {data['benchmark_return_pct']}%",
                    f"- Sharpe ratio: {data['sharpe_ratio']}",
                    f"- Max drawdown: {data['max_drawdown_pct']}%",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    f"- Unavailable: {portfolio['error']}",
                    f"- Message: {portfolio['message']}",
                    "",
                ]
            )

    lines.extend(["## Recent Trades", ""])
    trades = report.get("trade_history", [])
    if trades:
        lines.extend(
            [
                "| Time | Symbol | Side | Qty | Price | Total | Status |",
                "| --- | --- | --- | ---: | ---: | ---: | --- |",
            ]
        )
        for trade in trades:
            lines.append(
                "| {timestamp} | {symbol} | {side} | {quantity} | ${price} | ${total} | {status} |".format(
                    **trade
                )
            )
    else:
        lines.append("No trades found.")

    return "\n".join(lines) + "\n"
