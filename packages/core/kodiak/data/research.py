"""Research data providers for fundamentals and benchmark context."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

FUNDAMENTAL_FIELDS = {
    "market_cap",
    "enterprise_value",
    "pe_ratio",
    "forward_pe_ratio",
    "price_to_sales",
    "price_to_book",
    "dividend_yield_pct",
    "beta",
    "eps_ttm",
    "revenue_ttm",
    "gross_margin_pct",
    "operating_margin_pct",
    "profit_margin_pct",
    "debt_to_equity",
    "return_on_equity_pct",
    "free_cash_flow",
    "shares_outstanding",
}


@dataclass
class FundamentalRecord:
    """Normalized company fundamentals for one symbol."""

    symbol: str
    source: str = "file"
    as_of: str | None = None
    currency: str | None = None
    market_cap: Decimal | None = None
    enterprise_value: Decimal | None = None
    pe_ratio: Decimal | None = None
    forward_pe_ratio: Decimal | None = None
    price_to_sales: Decimal | None = None
    price_to_book: Decimal | None = None
    dividend_yield_pct: Decimal | None = None
    beta: Decimal | None = None
    eps_ttm: Decimal | None = None
    revenue_ttm: Decimal | None = None
    gross_margin_pct: Decimal | None = None
    operating_margin_pct: Decimal | None = None
    profit_margin_pct: Decimal | None = None
    debt_to_equity: Decimal | None = None
    return_on_equity_pct: Decimal | None = None
    free_cash_flow: Decimal | None = None
    shares_outstanding: Decimal | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class FileFundamentalsProvider:
    """Load fundamentals from JSON or CSV files.

    Supported layouts:
    - {data_dir}/{SYMBOL}.json
    - {data_dir}/fundamentals.json with a top-level symbol map
    - {data_dir}/fundamentals.csv with a `symbol` column
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)

    def get_fundamentals(self, symbol: str) -> FundamentalRecord:
        """Return normalized fundamentals for a symbol."""
        symbol = symbol.upper()
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Fundamentals data directory not found: {self.data_dir}")

        data = self._load_symbol_json(symbol)
        if data is None:
            data = self._load_json_map(symbol)
        if data is None:
            data = self._load_csv_row(symbol)
        if data is None:
            raise FileNotFoundError(f"No fundamentals found for {symbol} in {self.data_dir}")

        return _record_from_mapping(symbol, data)

    def _load_symbol_json(self, symbol: str) -> dict[str, Any] | None:
        file_path = self.data_dir / f"{symbol}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"{file_path} must contain a JSON object")
        return data

    def _load_json_map(self, symbol: str) -> dict[str, Any] | None:
        file_path = self.data_dir / "fundamentals.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"{file_path} must contain a JSON object")
        row = data.get(symbol) or data.get(symbol.lower())
        if row is None:
            return None
        if not isinstance(row, dict):
            raise ValueError(f"{file_path} entry for {symbol} must be a JSON object")
        return row

    def _load_csv_row(self, symbol: str) -> dict[str, Any] | None:
        file_path = self.data_dir / "fundamentals.csv"
        if not file_path.exists():
            return None
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("symbol") or "").upper() == symbol:
                    return dict(row)
        return None


def _record_from_mapping(symbol: str, data: dict[str, Any]) -> FundamentalRecord:
    normalized = {str(key).lower(): value for key, value in data.items()}
    metadata = {
        key: value
        for key, value in normalized.items()
        if key not in FUNDAMENTAL_FIELDS | {"symbol", "source", "as_of", "currency"}
    }
    field_values = {
        field_name: _decimal_or_none(normalized.get(field_name))
        for field_name in FUNDAMENTAL_FIELDS
    }
    return FundamentalRecord(
        symbol=symbol,
        source=str(normalized.get("source") or "file"),
        as_of=_string_or_none(normalized.get("as_of")),
        currency=_string_or_none(normalized.get("currency")),
        metadata=metadata,
        **field_values,
    )


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid decimal value: {value}") from exc
