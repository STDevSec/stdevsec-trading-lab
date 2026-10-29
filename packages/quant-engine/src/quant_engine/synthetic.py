"""Deterministic synthetic OHLCV generator.

Given a fixed seed it always produces the exact same dataset, and that dataset
always passes :func:`quant_engine.validation.validate_ohlcv`. Prices follow a
simple geometric Brownian motion; intrabar high/low are derived so every candle
is internally consistent.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_SEED = 42
DEFAULT_ROWS = 500
DEFAULT_FREQ = "1h"
DEFAULT_START = "2024-01-01T00:00:00Z"


def generate_ohlcv(
    *,
    rows: int = DEFAULT_ROWS,
    seed: int = DEFAULT_SEED,
    start: str = DEFAULT_START,
    freq: str = DEFAULT_FREQ,
    base_price: float = 100.0,
    mu: float = 0.0,
    sigma: float = 0.01,
) -> pd.DataFrame:
    """Return a deterministic, valid OHLCV ``DataFrame`` with ``rows`` candles."""
    if rows <= 0:
        raise ValueError("rows must be positive")
    if base_price <= 0:
        raise ValueError("base_price must be positive")

    rng = np.random.default_rng(seed)

    # Close prices via GBM; stays strictly positive by construction.
    log_returns = rng.normal(loc=mu, scale=sigma, size=rows)
    close = base_price * np.exp(np.cumsum(log_returns))

    # Open = previous close (first open = base_price). No lookahead.
    open_ = np.empty(rows, dtype=float)
    open_[0] = base_price
    open_[1:] = close[:-1]

    # Intrabar extension: high/low wrap the open/close range, always consistent.
    span = np.abs(rng.normal(loc=0.0, scale=sigma, size=rows)) * close
    body_hi = np.maximum(open_, close)
    body_lo = np.minimum(open_, close)
    high = body_hi + span
    low = np.maximum(body_lo - span, base_price * 1e-6)  # keep strictly positive

    volume = rng.integers(low=1, high=10_000, size=rows).astype("int64")

    timestamps = pd.date_range(start=pd.Timestamp(start), periods=rows, freq=freq, tz="UTC")

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic OHLCV data.")
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--freq", default=DEFAULT_FREQ)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write CSV here. If omitted, prints the first rows to stdout.",
    )
    args = parser.parse_args(argv)

    df = generate_ohlcv(rows=args.rows, seed=args.seed, start=args.start, freq=args.freq)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # ISO 8601 with tz so re-reading preserves timezone awareness.
        df.to_csv(args.out, index=False, date_format="%Y-%m-%dT%H:%M:%S%z")
        print(f"Wrote {len(df)} rows (seed={args.seed}) to {args.out}")
    else:
        print(df.head().to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
