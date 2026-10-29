from __future__ import annotations

from typing import Any

from quant_engine import generate_ohlcv


def dataset_payload(*, rows: int = 60, seed: int = 1, name: str = "Test") -> dict[str, Any]:
    """A valid dataset payload built from deterministic synthetic OHLCV."""
    df = generate_ohlcv(rows=rows, seed=seed)
    candles = [
        {
            "timestamp": ts.isoformat(),
            "open": float(o),
            "high": float(h),
            "low": float(low),
            "close": float(c),
            "volume": int(v),
        }
        for ts, o, h, low, c, v in zip(
            df["timestamp"], df["open"], df["high"], df["low"], df["close"], df["volume"],
            strict=True,
        )
    ]
    return {"name": name, "symbol": "TEST", "timeframe": "1h", "candles": candles}


def csv_bytes(*, rows: int = 60, seed: int = 1) -> bytes:
    """A valid OHLCV CSV (as upload bytes) from deterministic synthetic data."""
    df = generate_ohlcv(rows=rows, seed=seed)
    lines = ["timestamp,open,high,low,close,volume"]
    for ts, o, h, low, c, v in zip(
        df["timestamp"], df["open"], df["high"], df["low"], df["close"], df["volume"],
        strict=True,
    ):
        lines.append(f"{ts.isoformat()},{o},{h},{low},{c},{int(v)}")
    return ("\n".join(lines) + "\n").encode()
