from __future__ import annotations

import numpy as np
import pandas as pd

from quant_engine.synthetic import generate_ohlcv
from quant_engine.validation import Severity, validate_ohlcv


def _good() -> pd.DataFrame:
    return generate_ohlcv(rows=20, seed=42)


def _codes(df: pd.DataFrame) -> set[str]:
    return {i.code for i in validate_ohlcv(df).issues}


def test_good_dataset_is_valid() -> None:
    assert validate_ohlcv(_good()).is_valid


def test_missing_columns() -> None:
    df = _good().drop(columns=["volume"])
    report = validate_ohlcv(df)
    assert not report.is_valid
    assert "missing_columns" in {i.code for i in report.issues}


def test_empty_dataset() -> None:
    df = _good().iloc[0:0]
    assert "empty_dataset" in _codes(df)


def test_naive_timestamps_rejected() -> None:
    df = _good()
    df["timestamp"] = df["timestamp"].dt.tz_localize(None)
    assert "timestamp_not_tz_aware" in _codes(df)


def test_duplicate_timestamps() -> None:
    df = _good()
    df.loc[df.index[1], "timestamp"] = df.loc[df.index[0], "timestamp"]
    assert "duplicate_timestamps" in _codes(df)


def test_unordered_timestamps() -> None:
    df = _good()
    df = df.iloc[::-1].reset_index(drop=True)
    assert "timestamps_not_increasing" in _codes(df)


def test_missing_values() -> None:
    df = _good()
    df.loc[df.index[2], "close"] = np.nan
    assert "missing_values" in _codes(df)


def test_non_positive_price() -> None:
    df = _good()
    df.loc[df.index[3], "low"] = -1.0
    assert "invalid_price" in _codes(df)


def test_negative_volume() -> None:
    df = _good()
    df.loc[df.index[4], "volume"] = -10
    assert "negative_volume" in _codes(df)


def test_zero_volume_is_warning_only() -> None:
    df = _good()
    df.loc[df.index[5], "volume"] = 0
    report = validate_ohlcv(df)
    assert report.is_valid  # warning does not invalidate
    assert any(i.code == "zero_volume" and i.severity is Severity.WARNING for i in report.issues)


def test_high_low_inconsistent() -> None:
    df = _good()
    # Force high below the open/close body.
    df.loc[df.index[6], "high"] = df.loc[df.index[6], "low"] - 1.0
    assert "high_low_inconsistent" in _codes(df)


def test_report_does_not_mutate_input() -> None:
    df = _good()
    before = df.copy(deep=True)
    validate_ohlcv(df)
    pd.testing.assert_frame_equal(df, before)
