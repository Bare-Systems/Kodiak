"""Research data providers for fundamentals and benchmark context."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date
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


@dataclass(frozen=True)
class FundamentalsIngestResult:
    """Summary of a fundamentals ingestion run."""

    records: list[FundamentalRecord]
    output_files: list[Path]

    @property
    def count(self) -> int:
        """Number of records ingested."""
        return len(self.records)


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


def ingest_fundamentals(
    input_path: Path,
    output_dir: Path,
    output_format: str = "json-map",
    max_age_days: int | None = None,
    today: date | None = None,
) -> FundamentalsIngestResult:
    """Validate and write fundamentals into a Kodiak-readable file layout."""
    records = load_fundamental_records(input_path)
    validate_fundamental_records(records, max_age_days=max_age_days, today=today)
    output_files = write_fundamental_records(records, output_dir, output_format=output_format)
    return FundamentalsIngestResult(records=records, output_files=output_files)


def load_fundamental_records(input_path: Path) -> list[FundamentalRecord]:
    """Load and normalize fundamentals from CSV or JSON input."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Fundamentals input not found: {input_path}")

    suffix = input_path.suffix.lower()
    if suffix == ".csv":
        rows = _load_input_csv(input_path)
    elif suffix == ".json":
        rows = _load_input_json(input_path)
    else:
        raise ValueError("Fundamentals input must be .csv or .json")

    records = [_record_from_mapping(_required_symbol(row), row) for row in rows]
    validate_fundamental_records(records)
    return records


def validate_fundamental_records(
    records: list[FundamentalRecord],
    max_age_days: int | None = None,
    today: date | None = None,
) -> None:
    """Validate duplicate symbols and optional freshness constraints."""
    if not records:
        raise ValueError("No fundamentals records found")

    seen: set[str] = set()
    for record in records:
        if record.symbol in seen:
            raise ValueError(f"Duplicate fundamentals symbol: {record.symbol}")
        seen.add(record.symbol)
        if max_age_days is not None:
            _validate_as_of_freshness(record, max_age_days, today=today)


def write_fundamental_records(
    records: list[FundamentalRecord],
    output_dir: Path,
    output_format: str = "json-map",
) -> list[Path]:
    """Write normalized fundamentals in a layout supported by FileFundamentalsProvider."""
    validate_fundamental_records(records)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if output_format == "json-map":
        output_path = output_dir / "fundamentals.json"
        payload = {record.symbol: record_to_mapping(record) for record in sorted(records, key=lambda r: r.symbol)}
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
        return [output_path]

    if output_format == "json-files":
        output_files = []
        for record in sorted(records, key=lambda r: r.symbol):
            output_path = output_dir / f"{record.symbol}.json"
            output_path.write_text(json.dumps(record_to_mapping(record), indent=2, sort_keys=True, default=str) + "\n")
            output_files.append(output_path)
        return output_files

    if output_format == "csv":
        output_path = output_dir / "fundamentals.csv"
        rows = [record_to_mapping(record) for record in sorted(records, key=lambda r: r.symbol)]
        fieldnames = sorted({key for row in rows for key in row})
        if "symbol" in fieldnames:
            fieldnames.remove("symbol")
        fieldnames = ["symbol", *fieldnames]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return [output_path]

    raise ValueError("output_format must be one of: json-map, json-files, csv")


def record_to_mapping(record: FundamentalRecord) -> dict[str, Any]:
    """Serialize a FundamentalRecord without dropping unknown metadata fields."""
    payload: dict[str, Any] = {
        "symbol": record.symbol,
        "source": record.source,
    }
    if record.as_of is not None:
        payload["as_of"] = record.as_of
    if record.currency is not None:
        payload["currency"] = record.currency

    for field_name in sorted(FUNDAMENTAL_FIELDS):
        value = getattr(record, field_name)
        if value is not None:
            payload[field_name] = value

    payload.update(record.metadata)
    return payload


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
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Invalid decimal value: {value}") from exc
    if not result.is_finite():
        raise ValueError(f"Invalid non-finite decimal value: {value}")
    return result


def _load_input_csv(input_path: Path) -> list[dict[str, Any]]:
    with open(input_path, newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _load_input_json(input_path: Path) -> list[dict[str, Any]]:
    with open(input_path) as f:
        data = json.load(f)

    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict) and "symbol" in {str(key).lower() for key in data}:
        rows = [data]
    elif isinstance(data, dict):
        rows = []
        for symbol, row in data.items():
            if not isinstance(row, dict):
                raise ValueError(f"Fundamentals entry for {symbol} must be a JSON object")
            rows.append({"symbol": symbol, **row})
    else:
        raise ValueError("JSON fundamentals input must be an object, symbol map, or list of objects")

    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("JSON fundamentals list must contain only objects")
    return rows


def _required_symbol(row: dict[str, Any]) -> str:
    symbol = _string_or_none(row.get("symbol"))
    if symbol is None:
        raise ValueError("Every fundamentals record must include a symbol")
    return symbol.upper()


def _validate_as_of_freshness(
    record: FundamentalRecord,
    max_age_days: int,
    today: date | None = None,
) -> None:
    if max_age_days < 0:
        raise ValueError("max_age_days must be non-negative")
    if record.as_of is None:
        raise ValueError(f"Fundamentals for {record.symbol} missing as_of")
    try:
        as_of = date.fromisoformat(record.as_of)
    except ValueError as exc:
        raise ValueError(f"Fundamentals for {record.symbol} has invalid as_of: {record.as_of}") from exc
    reference_date = today or date.today()
    if (reference_date - as_of).days > max_age_days:
        raise ValueError(
            f"Fundamentals for {record.symbol} are stale: as_of={record.as_of}, "
            f"max_age_days={max_age_days}"
        )
