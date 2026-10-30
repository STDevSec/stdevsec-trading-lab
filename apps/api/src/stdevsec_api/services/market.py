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
_SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,20}$")


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
