"""Performance analytics over a :class:`~quant_engine.backtest.BacktestResult`.

Every metric below documents its formula, assumptions and limitations. Metrics
that are undefined for the given data (e.g. win rate with zero trades) return
``None`` rather than a misleading number. Nothing here fabricates results.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from quant_engine.backtest import BacktestResult

_SECONDS_PER_YEAR = 365.25 * 24 * 3600


@dataclass
class Metrics:
    n_trades: int
    win_rate: float | None  # wins / trades
    profit_factor: float | None  # gross profit / gross loss; inf if no losses
    expectancy: float | None  # mean P&L per trade
    avg_win: float | None  # mean P&L of winning trades
    avg_loss: float | None  # mean P&L of losing trades (negative)
    net_profit: float  # final equity - initial capital
    total_return: float  # net_profit / initial capital
    max_drawdown: float  # largest peak-to-trough equity decline, as a fraction >= 0
    sharpe: float | None  # annualized, risk-free = 0; None if not computable
    max_consecutive_wins: int
    max_consecutive_losses: int


def max_drawdown(equity: pd.Series) -> float:
    """Largest peak-to-trough decline of ``equity`` as a non-negative fraction.

    Assumption: ``equity`` is marked to market in order. 0.0 if it never drops.
    """
    if len(equity) == 0:
        return 0.0
    running_peak = equity.cummax()
    drawdown = equity / running_peak - 1.0
    return float(-drawdown.min())


def sharpe_ratio(equity: pd.Series, *, periods_per_year: float | None = None) -> float | None:
    """Annualized Sharpe of per-bar returns, risk-free rate assumed 0.

    Formula: ``mean(r) / std(r) * sqrt(periods_per_year)`` where ``r`` are
    simple per-bar returns. ``periods_per_year`` is inferred from the timestamp
    spacing when omitted.

    Limitations: needs enough bars to be meaningful (returns ``None`` for < 2
    returns or zero volatility); assumes roughly i.i.d. returns, which real
    strategies violate — treat as indicative, not a guarantee.
    """
    returns = equity.pct_change().dropna()
    if len(returns) < 2:
        return None
    std = float(returns.std(ddof=1))
    if std == 0 or math.isnan(std):
        return None
    mean = float(returns.mean())

    if periods_per_year is None:
        periods_per_year = _infer_periods_per_year(equity.index)
    annualization = math.sqrt(periods_per_year) if periods_per_year else 1.0
    return mean / std * annualization


def monthly_returns(equity: pd.Series) -> pd.Series:
    """Calendar-month returns from the equity curve (requires a datetime index)."""
    if not isinstance(equity.index, pd.DatetimeIndex):
        raise TypeError("equity must have a DatetimeIndex for monthly returns")
    month_end = equity.resample("ME").last()
    return month_end.pct_change().dropna()


def _infer_periods_per_year(index: pd.Index) -> float | None:
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        return None
    deltas = index.to_series().diff().dropna()
    median_seconds = float(deltas.dt.total_seconds().median())
    if median_seconds <= 0:
        return None
    return _SECONDS_PER_YEAR / median_seconds


def _max_streak(pnls: list[float], *, winning: bool) -> int:
    best = current = 0
    for p in pnls:
        hit = p > 0 if winning else p < 0
        current = current + 1 if hit else 0
        best = max(best, current)
    return best


def compute_metrics(
    result: BacktestResult, *, periods_per_year: float | None = None
) -> Metrics:
    """Compute the full metric set for a backtest result."""
    pnls = [rt.pnl for rt in result.round_trips]
    n = len(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    gross_profit = sum(wins)
    gross_loss = -sum(losses)  # positive magnitude
    if n == 0:
        profit_factor: float | None = None
    elif gross_loss == 0:
        profit_factor = math.inf
    else:
        profit_factor = gross_profit / gross_loss

    net_profit = result.final_equity - result.initial_capital

    return Metrics(
        n_trades=n,
        win_rate=(len(wins) / n) if n else None,
        profit_factor=profit_factor,
        expectancy=(sum(pnls) / n) if n else None,
        avg_win=(sum(wins) / len(wins)) if wins else None,
        avg_loss=(sum(losses) / len(losses)) if losses else None,
        net_profit=net_profit,
        total_return=result.total_return,
        max_drawdown=max_drawdown(result.equity),
        sharpe=sharpe_ratio(result.equity, periods_per_year=periods_per_year),
        max_consecutive_wins=_max_streak(pnls, winning=True),
        max_consecutive_losses=_max_streak(pnls, winning=False),
    )
