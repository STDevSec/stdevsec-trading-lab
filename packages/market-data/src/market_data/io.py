"""Safe market-data IO.

Everything here assumes the file and its contents are **untrusted**:

* uploads are size-capped before parsing (resource exhaustion),
* user-supplied paths are confined under a base directory (path traversal),
* CSV text cells are neutralized on export (CSV/formula injection),
* only data formats are parsed — never code; ``pickle`` is never used.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

#: Default upload/parse cap: 50 MiB.
DEFAULT_MAX_BYTES = 50 * 1024 * 1024

#: Leading characters a spreadsheet may interpret as a formula.
_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class DatasetTooLargeError(ValueError):
    """Raised when a file exceeds the configured byte cap."""


def safe_resolve(base: Path | str, user_path: str) -> Path:
    """Resolve ``user_path`` strictly inside ``base``.

    Rejects absolute paths and ``..`` traversal that would escape ``base``.
    """
    base_resolved = Path(base).resolve()
    candidate = (base_resolved / user_path).resolve()
    if base_resolved != candidate and base_resolved not in candidate.parents:
        raise ValueError(f"Path escapes base directory: {user_path!r}")
    return candidate


def neutralize_csv_value(value: object) -> object:
    """Prefix a text cell with ``'`` if it could be read as a spreadsheet formula.

    Non-string values are returned unchanged.
    """
    if isinstance(value, str) and value.startswith(_INJECTION_PREFIXES):
        return "'" + value
    return value


def read_ohlcv_csv(
    path: Path | str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timestamp_column: str = "timestamp",
) -> pd.DataFrame:
    """Read an OHLCV CSV with a size cap and UTC-normalized timestamps.

    Does not validate data quality — pass the result to
    :func:`quant_engine.validate_ohlcv`. Does not repair anything.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Not a regular file: {p}")

    size = p.stat().st_size
    if size > max_bytes:
        raise DatasetTooLargeError(f"File is {size} bytes, exceeds cap of {max_bytes} bytes.")

    # engine="c", no python eval, no index inference surprises.
    df = pd.read_csv(p)
    return _normalize_timestamps(df, timestamp_column)


def read_ohlcv_csv_bytes(
    data: bytes,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    timestamp_column: str = "timestamp",
) -> pd.DataFrame:
    """Parse an uploaded OHLCV CSV from in-memory bytes.

    Same contract as :func:`read_ohlcv_csv` but for an upload that never touches
    disk: the byte cap is checked before parsing. Does not validate data quality.
    """
    if len(data) > max_bytes:
        raise DatasetTooLargeError(f"Upload is {len(data)} bytes, exceeds cap of {max_bytes}.")
    df = pd.read_csv(io.BytesIO(data))
    return _normalize_timestamps(df, timestamp_column)


def _normalize_timestamps(df: pd.DataFrame, timestamp_column: str) -> pd.DataFrame:
    """Parse the timestamp column to UTC in place (unparseable -> NaT)."""
    if timestamp_column in df.columns:
        df[timestamp_column] = pd.to_datetime(
            df[timestamp_column], utc=True, errors="coerce", format="ISO8601"
        )
    return df


def write_ohlcv_csv(df: pd.DataFrame, path: Path | str) -> None:
    """Write ``df`` to CSV, neutralizing CSV-injection in text columns."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    safe = df.copy()
    for col in safe.columns:
        # Detect by value, not dtype: a string column may be object or an
        # extension dtype (e.g. pyarrow-backed) depending on pandas config.
        if safe[col].map(lambda v: isinstance(v, str)).any():
            safe[col] = safe[col].map(neutralize_csv_value)

    safe.to_csv(p, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
