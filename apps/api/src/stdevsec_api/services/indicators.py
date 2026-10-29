"""Compute a fixed bundle of indicators for a dataset's latest version.

Fixed sensible defaults (no per-request params yet — add when a user needs to
tune windows). All NaN become ``None`` so the payload is JSON-safe.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from quant_engine import bollinger, ema, macd, rsi, sma
from stdevsec_api.services.datasets import get_dataset, latest_version
from stdevsec_api.services.ohlcv import candles_to_df


def _clean(series: pd.Series) -> list[float | None]:
    return [None if not math.isfinite(v) else float(v) for v in series.to_numpy(dtype=float)]


def ohlcv_with_indicators(db: Session, dataset_id: str) -> dict[str, Any]:
    dataset = get_dataset(db, dataset_id)
    version = latest_version(dataset)
    df = candles_to_df(version.candles)
    close = df["close"]

    macd_line, macd_signal, macd_hist = macd(close)
    bb_mid, bb_upper, bb_lower = bollinger(close)

    candles = [
        {
            "time": int(ts.timestamp()),
            "open": float(o),
            "high": float(h),
            "low": float(low),
            "close": float(c),
            "volume": float(v),
        }
        for ts, o, h, low, c, v in zip(
            df["timestamp"], df["open"], df["high"], df["low"], df["close"], df["volume"],
            strict=True,
        )
    ]
    indicators = {
        "sma20": _clean(sma(close, 20)),
        "sma50": _clean(sma(close, 50)),
        "ema20": _clean(ema(close, 20)),
        "bb_upper": _clean(bb_upper),
        "bb_mid": _clean(bb_mid),
        "bb_lower": _clean(bb_lower),
        "rsi14": _clean(rsi(close, 14)),
        "macd": _clean(macd_line),
        "macd_signal": _clean(macd_signal),
        "macd_hist": _clean(macd_hist),
    }
    return {"candles": candles, "indicators": indicators}
