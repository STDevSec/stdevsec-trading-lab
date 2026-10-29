"""Technical indicators (pure, deterministic, no lookahead).

Each function takes a close-price Series (or OHLCV DataFrame) and returns a
Series/tuple aligned to the input index. Warm-up periods are NaN — never filled
or back-propagated, so nothing leaks future information.
"""

from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return close.rolling(window).mean()


def ema(close: pd.Series, span: int) -> pd.Series:
    """Exponential moving average (no warm-up adjustment)."""
    return close.ewm(span=span, adjust=False).mean()


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's Relative Strength Index in [0, 100]."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # Wilder smoothing == EMA with alpha = 1/window.
    avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss
    out = 100.0 - 100.0 / (1.0 + rs)
    # All-gains window -> avg_loss 0 -> rs inf -> rsi 100 (pandas yields NaN there).
    out = out.where(avg_loss != 0, 100.0).where(avg_gain.notna())
    return out


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD line, signal line, and histogram."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def bollinger(
    close: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands: (middle SMA, upper, lower)."""
    mid = sma(close, window)
    std = close.rolling(window).std(ddof=0)
    return mid, mid + num_std * std, mid - num_std * std
