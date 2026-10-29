"""Generate the deterministic sample dataset the web chart renders.

Writes a JSON array of candles (``time`` as Unix seconds, UTC) to the web app's
public folder. Reproducible: same seed -> byte-identical output.

    uv run python scripts/gen_sample.py
"""

from __future__ import annotations

import json
from pathlib import Path

from quant_engine import generate_ohlcv, validate_ohlcv

OUT = Path(__file__).resolve().parent.parent / "apps" / "web" / "public" / "sample-ohlcv.json"
ROWS = 300
SEED = 42


def main() -> int:
    df = generate_ohlcv(rows=ROWS, seed=SEED)

    report = validate_ohlcv(df)
    if not report.is_valid:  # never ship data the engine rejects
        for issue in report.errors:
            print(f"ERROR {issue.code}: {issue.message}")
        return 1

    records = [
        {
            "time": int(ts.timestamp()),
            "open": round(float(o), 4),
            "high": round(float(h), 4),
            "low": round(float(low), 4),
            "close": round(float(c), 4),
            "volume": int(v),
        }
        for ts, o, h, low, c, v in zip(
            df["timestamp"], df["open"], df["high"], df["low"], df["close"], df["volume"],
            strict=True,
        )
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, indent=2) + "\n")
    print(f"Wrote {len(records)} candles (seed={SEED}) to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
