"""Deterministic, event-driven backtester (long/flat, single asset).

Execution model (see ADR-0005): a target weight decided at the **close of bar
``t-1``** is executed at the **open of bar ``t``**. A signal can therefore never
execute on the same bar that produced it — there is no look-ahead. Equity is
marked to market at each bar's close.

Costs are explicit: ``commission_bps`` on traded notional and ``slippage_bps``
moving the fill against the trade (buys fill higher, sells fill lower).

Risk (see ADR-0006): an optional ``max_drawdown_halt`` liquidates and stays flat
once equity falls that fraction below its peak.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from quant_engine.strategy import Strategy

_EPS = 1e-9


@dataclass(frozen=True)
class Trade:
    """A single fill (one leg)."""

    timestamp: pd.Timestamp
    side: str  # "buy" | "sell"
    units: float
    price: float  # fill price, slippage included
    commission: float


@dataclass(frozen=True)
class RoundTrip:
    """A completed long position (entry buy to the sell that returns to flat)."""

    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    units: float
    entry_price: float
    exit_price: float
    pnl: float  # realized P&L net of both legs' commissions
    return_pct: float  # pnl / entry cost


@dataclass
class BacktestResult:
    equity: pd.Series  # marked to market at each bar close, indexed by timestamp
    trades: list[Trade]
    initial_capital: float
    round_trips: list[RoundTrip] = field(default_factory=list)

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
    max_drawdown_halt: float | None = None,
) -> BacktestResult:
    """Run a long/flat backtest of ``signals`` (target weights) over ``df``.

    ``df`` must be validated OHLCV (``timestamp``, ``open``, ``close`` used here).
    ``signals[t]`` is the weight decided at the close of bar ``t``; it takes
    effect at the open of bar ``t+1``. If ``max_drawdown_halt`` is set and equity
    drops that fraction below its running peak, trading halts (flat) for the rest
    of the run.
    """
    if capital <= 0:
        raise ValueError("capital must be positive")
    if max_drawdown_halt is not None and not (0 < max_drawdown_halt <= 1):
        raise ValueError("max_drawdown_halt must be in (0, 1]")
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
    peak_equity = capital
    halted = False
    equity_curve: list[float] = []
    trades: list[Trade] = []
    round_trips: list[RoundTrip] = []
    entry: Trade | None = None

    for t in range(n):
        if t > 0:
            target_weight = 0.0 if halted else weights[t - 1]
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
                leg = Trade(
                    timestamp=pd.Timestamp(timestamps[t]),
                    side="buy" if is_buy else "sell",
                    units=abs(delta),
                    price=fill,
                    commission=commission,
                )
                trades.append(leg)

                if is_buy and entry is None:
                    entry = leg
                elif not is_buy and entry is not None and units < _EPS:
                    # Position fully closed -> realize a round trip.
                    entry_cost = entry.units * entry.price + entry.commission
                    exit_proceeds = leg.units * leg.price - leg.commission
                    pnl = exit_proceeds - entry_cost
                    round_trips.append(
                        RoundTrip(
                            entry_time=entry.timestamp,
                            exit_time=leg.timestamp,
                            units=leg.units,
                            entry_price=entry.price,
                            exit_price=leg.price,
                            pnl=pnl,
                            return_pct=pnl / entry_cost,
                        )
                    )
                    entry = None

        equity_t = cash + units * closes[t]
        equity_curve.append(equity_t)
        peak_equity = max(peak_equity, equity_t)
        if max_drawdown_halt is not None and peak_equity > 0:
            if (equity_t / peak_equity - 1.0) <= -max_drawdown_halt:
                halted = True

    equity = pd.Series(equity_curve, index=pd.Index(timestamps, name="timestamp"), name="equity")
    return BacktestResult(
        equity=equity,
        trades=trades,
        initial_capital=capital,
        round_trips=round_trips,
    )


def backtest_strategy(
    df: pd.DataFrame,
    strategy: Strategy,
    *,
    capital: float = 10_000.0,
    commission_bps: float = 0.0,
    slippage_bps: float = 0.0,
    max_drawdown_halt: float | None = None,
) -> BacktestResult:
    """Convenience: generate signals from ``strategy`` and backtest them."""
    signals = strategy.generate_signals(df)
    return run_backtest(
        df,
        signals,
        capital=capital,
        commission_bps=commission_bps,
        slippage_bps=slippage_bps,
        max_drawdown_halt=max_drawdown_halt,
    )
