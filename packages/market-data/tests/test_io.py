from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from market_data import (
    DatasetTooLargeError,
    neutralize_csv_value,
    read_ohlcv_csv,
    safe_resolve,
    write_ohlcv_csv,
)
from quant_engine import generate_ohlcv, validate_ohlcv


def test_roundtrip_csv_stays_valid(tmp_path: Path) -> None:
    df = generate_ohlcv(rows=50, seed=42)
    out = tmp_path / "data.csv"
    write_ohlcv_csv(df, out)
    back = read_ohlcv_csv(out)
    assert validate_ohlcv(back).is_valid


def test_size_cap_enforced(tmp_path: Path) -> None:
    f = tmp_path / "big.csv"
    f.write_text("timestamp,open,high,low,close,volume\n")
    with pytest.raises(DatasetTooLargeError):
        read_ohlcv_csv(f, max_bytes=1)


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_ohlcv_csv(tmp_path / "nope.csv")


def test_timestamps_parsed_to_utc(tmp_path: Path) -> None:
    out = tmp_path / "d.csv"
    write_ohlcv_csv(generate_ohlcv(rows=5, seed=1), out)
    back = read_ohlcv_csv(out)
    assert str(back["timestamp"].dt.tz) == "UTC"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("=1+1", "'=1+1"),
        ("+cmd", "'+cmd"),
        ("-2", "'-2"),
        ("@SUM", "'@SUM"),
        ("safe", "safe"),
        (123, 123),
    ],
)
def test_csv_injection_neutralized(raw: object, expected: object) -> None:
    assert neutralize_csv_value(raw) == expected


def test_injection_neutralized_on_write(tmp_path: Path) -> None:
    out = tmp_path / "inj.csv"
    write_ohlcv_csv(pd.DataFrame({"note": ["=HYPERLINK(1)"]}), out)
    assert out.read_text().splitlines()[1].startswith("'=HYPERLINK")


def test_safe_resolve_allows_inside(tmp_path: Path) -> None:
    assert safe_resolve(tmp_path, "sub/file.csv") == (tmp_path / "sub/file.csv").resolve()


def test_safe_resolve_blocks_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        safe_resolve(tmp_path, "../../etc/passwd")
