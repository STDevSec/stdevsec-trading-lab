from __future__ import annotations

import numpy as np
import pandas as pd

from quant_engine import bollinger, ema, generate_ohlcv, macd, rsi, sma


def test_sma_values_and_warmup() -> None:
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    out = sma(s, 3)
    assert out[:2].isna().all()  # warm-up is NaN, never filled
    assert out.iloc[2] == 2.0 and out.iloc[4] == 4.0


def test_ema_first_equals_price() -> None:
    s = pd.Series([10.0, 11.0, 12.0])
    out = ema(s, 2)
    assert out.iloc[0] == 10.0  # adjust=False seeds with first value


def test_rsi_bounds_and_trend() -> None:
    up = pd.Series(np.arange(1, 50, dtype=float))  # strictly increasing
    r = up.pipe(rsi, 14).dropna()
    assert ((r >= 0) & (r <= 100)).all()
    assert r.iloc[-1] > 99  # all gains -> RSI saturates near 100

    down = pd.Series(np.arange(50, 1, -1, dtype=float))
    rd = rsi(down, 14).dropna()
    assert rd.iloc[-1] < 1  # all losses -> near 0


def test_macd_histogram_identity() -> None:
    close = generate_ohlcv(rows=80, seed=5)["close"]
    line, signal, hist = macd(close)
    assert np.allclose((line - signal).dropna(), hist.dropna())


def test_bollinger_ordering() -> None:
    close = generate_ohlcv(rows=60, seed=3)["close"]
    mid, upper, lower = bollinger(close, 20, 2.0)
    valid = mid.notna()
    assert (upper[valid] >= mid[valid]).all()
    assert (mid[valid] >= lower[valid]).all()
    assert np.allclose(mid.dropna(), sma(close, 20).dropna())  # mid is the SMA
