"""Live spot price lookup for paper trading.

Uses Binance's public ticker (no API key). Simulation-only: this price feeds a
paper fill, never a real order. Network/parse failures surface as UpstreamError.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from stdevsec_api.errors import DomainValidationError, UpstreamError

_BINANCE_PRICE = "https://api.binance.com/api/v3/ticker/price"
_BINANCE_KLINES = "https://api.binance.com/api/v3/klines"
_SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,20}$")
# Only intervals we expose; keeps the upstream query bounded and validated.
_INTERVALS = frozenset({"1m", "5m", "15m", "1h", "4h", "1d"})


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not _SYMBOL_RE.match(s):
        raise DomainValidationError(f"Invalid symbol: {symbol!r}")
    return s


def fetch_price(symbol: str) -> float:
    """Current spot price for ``symbol`` (e.g. BTCUSDT) from Binance."""
    s = validate_symbol(symbol)
    url = f"{_BINANCE_PRICE}?symbol={s}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 (fixed https host)
            data = json.load(resp)
        return float(data["price"])
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
        raise UpstreamError(f"No se pudo obtener el precio de {s}: {exc}") from exc


def fetch_klines(symbol: str, interval: str = "1m", limit: int = 200) -> list[dict[str, float]]:
    """Recent candles for ``symbol`` from Binance, newest last.

    Returns dicts shaped for ``OhlcvCandle`` (time in unix seconds). Feeds the
    live chart only; simulation-only like :func:`fetch_price`.
    """
    s = validate_symbol(symbol)
    if interval not in _INTERVALS:
        raise DomainValidationError(f"Invalid interval: {interval!r}")
    lim = max(1, min(int(limit), 500))
    url = f"{_BINANCE_KLINES}?symbol={s}&interval={interval}&limit={lim}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 (fixed https host)
            rows = json.load(resp)
        # Binance kline row: [openTime(ms), open, high, low, close, volume, ...]
        return [
            {
                "time": int(r[0]) // 1000,
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
            }
            for r in rows
        ]
    except (urllib.error.URLError, TimeoutError, IndexError, ValueError) as exc:
        raise UpstreamError(f"No se pudieron obtener velas de {s}: {exc}") from exc
