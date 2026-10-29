"""Trading strategies.

A strategy maps an OHLCV ``DataFrame`` to a target **long weight** in ``[0, 1]``
per bar. The weight for bar ``t`` is decided using information available up to
and including the **close of bar ``t``** — never later. The backtester is what
turns a weight decided at a close into a fill at the next bar's open, so
strategies here carry no look-ahead by construction.

Sprint 02 covers long/flat strategies (weight 0 or 1). Fractional sizing and
shorting are left to later sprints.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    """Base class: produce a target long weight per bar, aligned to ``df.index``."""

    name: str

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return a ``Series`` of target weights in ``[0, 1]`` indexed like ``df``.

        ``signals[t]`` may depend only on data up to and including ``df`` row
        ``t`` (its close). No future information.
        """


class BuyAndHold(Strategy):
    """Always fully invested. Enters at the first executable bar and holds."""

    name = "buy_and_hold"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        return pd.Series(1.0, index=df.index, name="weight")


class SMACrossover(Strategy):
    """Long while the fast SMA is above the slow SMA, flat otherwise.

    Both moving averages use closing prices up to the current bar, so the signal
    is known at that bar's close. During the warm-up (before ``slow`` bars exist)
    the strategy stays flat.
    """

    def __init__(self, fast: int = 10, slow: int = 30) -> None:
        if fast < 1 or slow < 1:
            raise ValueError("SMA windows must be >= 1")
        if fast >= slow:
            raise ValueError("fast window must be strictly less than slow window")
        self.fast = fast
        self.slow = slow
        self.name = f"sma_crossover_{fast}_{slow}"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        fast_ma = close.rolling(self.fast).mean()
        slow_ma = close.rolling(self.slow).mean()
        # NaN during warm-up -> comparison is False -> flat.
        signals = (fast_ma > slow_ma).astype(float)
        signals.name = "weight"
        return signals
