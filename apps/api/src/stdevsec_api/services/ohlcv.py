"""Conversions between API/stored candles, DataFrames, and JSON-safe results."""

from __future__ import annotations

import math
from dataclasses import asdict
from typing import Any

import pandas as pd
from pydantic import ValidationError

from quant_engine import Metrics, ValidationReport
from stdevsec_api.errors import DomainValidationError
from stdevsec_api.schemas import CandleIn

_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def candles_from_df(df: pd.DataFrame) -> list[CandleIn]:
    """Build validated API candles from a parsed CSV DataFrame.

    Timestamps are already UTC-parsed by the reader (unparseable -> NaT). Raises
    ``DomainValidationError`` on missing columns or any bad row, naming the row —
    quality checks (gaps, monotonicity, OHLC sanity) run later via the engine.
    """
    missing = [c for c in _COLUMNS if c not in df.columns]
    if missing:
        raise DomainValidationError(
            "CSV is missing required columns",
            details={"missing": missing, "required": _COLUMNS},
        )

    out: list[CandleIn] = []
    for i, rec in enumerate(df[_COLUMNS].to_dict("records")):
        ts = rec["timestamp"]
        if pd.isna(ts):
            raise DomainValidationError(f"Row {i}: unparseable timestamp", details={"row": i})
        try:
            out.append(
                CandleIn(
                    timestamp=ts.to_pydatetime(),
                    open=float(rec["open"]),
                    high=float(rec["high"]),
                    low=float(rec["low"]),
                    close=float(rec["close"]),
                    volume=float(rec["volume"]),
                )
            )
        except (ValidationError, TypeError, ValueError) as exc:
            raise DomainValidationError(
                f"Row {i}: invalid candle", details={"row": i, "error": str(exc)}
            ) from exc
    return out


def candles_from_models(candles: list[CandleIn]) -> pd.DataFrame:
    """Build a validated-shape DataFrame from incoming API candles."""
    records = [
        {
            "timestamp": c.timestamp,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in candles
    ]
    df = pd.DataFrame(records, columns=_COLUMNS)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


def candles_to_storage(candles: list[CandleIn]) -> list[dict[str, Any]]:
    """Serialize candles for JSON storage (ISO-8601 UTC timestamps)."""
    return [
        {
            "timestamp": c.timestamp.isoformat(),
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        }
        for c in candles
    ]


def candles_to_df(stored: list[dict[str, Any]]) -> pd.DataFrame:
    """Rebuild a DataFrame from stored candle dicts."""
    df = pd.DataFrame(stored, columns=_COLUMNS)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, format="ISO8601")
    return df


def report_to_dict(report: ValidationReport) -> dict[str, Any]:
    return {
        "is_valid": report.is_valid,
        "n_rows": report.n_rows,
        "issues": [
            {
                "code": i.code,
                "severity": i.severity.value,
                "message": i.message,
                "count": i.count,
            }
            for i in report.issues
        ],
    }


def metrics_to_json(metrics: Metrics) -> dict[str, Any]:
    """Metrics as a JSON-safe dict (non-finite floats -> None)."""
    out: dict[str, Any] = {}
    for key, value in asdict(metrics).items():
        if isinstance(value, float) and not math.isfinite(value):
            out[key] = None
        else:
            out[key] = value
    return out
