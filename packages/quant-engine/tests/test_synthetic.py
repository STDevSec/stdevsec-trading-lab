from __future__ import annotations

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from quant_engine.synthetic import generate_ohlcv
from quant_engine.validation import validate_ohlcv


def test_is_deterministic() -> None:
    a = generate_ohlcv(rows=200, seed=42)
    b = generate_ohlcv(rows=200, seed=42)
    pd.testing.assert_frame_equal(a, b)


def test_different_seed_differs() -> None:
    a = generate_ohlcv(rows=200, seed=1)
    b = generate_ohlcv(rows=200, seed=2)
    assert not a["close"].equals(b["close"])


def test_generated_data_is_valid() -> None:
    df = generate_ohlcv(rows=500, seed=42)
    report = validate_ohlcv(df)
    assert report.is_valid, [i.message for i in report.errors]


def test_timestamps_are_tz_aware_and_ordered() -> None:
    df = generate_ohlcv(rows=50, seed=7)
    assert df["timestamp"].dt.tz is not None
    assert df["timestamp"].is_monotonic_increasing


def test_open_equals_previous_close_no_lookahead() -> None:
    df = generate_ohlcv(rows=100, seed=3)
    # open[i] == close[i-1] (no information from the current candle leaks in)
    assert (df["open"].iloc[1:].to_numpy() == df["close"].iloc[:-1].to_numpy()).all()


@settings(max_examples=25, deadline=None)
@given(
    seed=st.integers(min_value=0, max_value=2**32 - 1),
    rows=st.integers(min_value=1, max_value=300),
)
def test_any_seed_produces_valid_data(seed: int, rows: int) -> None:
    report = validate_ohlcv(generate_ohlcv(rows=rows, seed=seed))
    assert report.is_valid, [i.message for i in report.errors]
