"""Deterministic, event-driven backtester (long/flat, single asset).

Execution model (see ADR-0005): a target weight decided at the **close of bar
``t-1``** is executed at the **open of bar ``t``**. A signal can therefore never
execute on the same bar that produced it — there is no look-ahead. Equity is
marked to market at each bar's close.

Costs are explicit: ``commission_bps`` on traded notional and ``slippage_bps``
moving the fill against the trade (buys fill higher, sells fill lower).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from quant_engine.strategy import Strategy

_EPS = 1e-9


@dataclass(frozen=True)
class Trade:
    timestamp: pd.Timestamp
    side: str  # "buy" | "sell"
    units: float
    price: float  # fill price, slippage included
    commission: float


@dataclass
class BacktestResult:
    equity: pd.Series  # marked to market at each bar close, indexed by timestamp
    trades: list[Trade]
    initial_capital: float

    @property
    def final_equity(self) -> float:
        return float(self.equity.iloc[-1])

    @property
    def total_return(self) -> float:
        return self.final_equity / self.initial_capital - 1.0


def run_backtest(
    df: pd.DataFrame,
    signals: pd.Series,
    *,
    capital: float = 10_000.0,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
) -> BacktestResult:
    """Run a long/flat backtest of ``signals`` (target weights) over ``df``.

    ``df`` must be validated OHLCV (``timestamp``, ``open``, ``close`` used here).
    ``signals[t]`` is the weight decided at the close of bar ``t``; it takes
    effect at the open of bar ``t+1``.
    """
    if capital <= 0:
        raise ValueError("capital must be positive")
    for col in ("timestamp", "open", "close"):
        if col not in df.columns:
            raise ValueError(f"df is missing required column '{col}'")

    opens = df["open"].to_numpy(dtype=float)
    closes = df["close"].to_numpy(dtype=float)
    timestamps = df["timestamp"].to_numpy()
    weights = signals.reindex(df.index).fillna(0.0).to_numpy(dtype=float)
    n = len(df)

    commission_rate = commission_bps / 10_000.0
    slippage_rate = slippage_bps / 10_000.0

    cash = capital
    units = 0.0
    equity_curve: list[float] = []
    trades: list[Trade] = []

    for t in range(n):
        if t > 0:
            target_weight = weights[t - 1]  # decided at close[t-1]
            open_px = opens[t]
            equity_at_open = cash + units * open_px
            target_units = (target_weight * equity_at_open) / open_px
            delta = target_units - units
            if abs(delta) > _EPS:
                is_buy = delta > 0
                fill = open_px * (1 + slippage_rate) if is_buy else open_px * (1 - slippage_rate)
                commission = abs(delta) * fill * commission_rate
                cash -= delta * fill  # buy (delta>0) spends; sell (delta<0) adds
                cash -= commission
                units = target_units
                trades.append(
                    Trade(
                        timestamp=pd.Timestamp(timestamps[t]),
                        side="buy" if is_buy else "sell",
                        units=abs(delta),
                        price=fill,
                        commission=commission,
                    )
                )
        equity_curve.append(cash + units * closes[t])

    equity = pd.Series(equity_curve, index=pd.Index(timestamps, name="timestamp"), name="equity")
    return BacktestResult(equity=equity, trades=trades, initial_capital=capital)


def backtest_strategy(
    df: pd.DataFrame,
    strategy: Strategy,
    *,
    capital: float = 10_000.0,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
) -> BacktestResult:
    """Convenience: generate signals from ``strategy`` and backtest them."""
    signals = strategy.generate_signals(df)
    return run_backtest(
        df,
        signals,
        capital=capital,
        commission_bps=commission_bps,
        slippage_bps=slippage_bps,
    )
