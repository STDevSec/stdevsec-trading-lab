from __future__ import annotations

import math

import pandas as pd
import pytest

from quant_engine.analytics import (
    compute_metrics,
    max_drawdown,
    monthly_returns,
    sharpe_ratio,
)
from quant_engine.backtest import BacktestResult, RoundTrip, backtest_strategy
from quant_engine.strategy import BuyAndHold
from quant_engine.synthetic import generate_ohlcv


def _equity(values: list[float]) -> pd.Series:
    idx = pd.date_range("2024-01-01", periods=len(values), freq="D", tz="UTC")
    return pd.Series(values, index=idx, name="equity")


def _round_trip(pnl: float, entry_cost: float = 1000.0) -> RoundTrip:
    ts = pd.Timestamp("2024-01-01", tz="UTC")
    return RoundTrip(
        entry_time=ts,
        exit_time=ts,
        units=1.0,
        entry_price=entry_cost,
        exit_price=entry_cost + pnl,
        pnl=pnl,
        return_pct=pnl / entry_cost,
    )


def _result(equity: list[float], pnls: list[float]) -> BacktestResult:
    eq = _equity(equity)
    return BacktestResult(
        equity=eq,
        trades=[],
        initial_capital=equity[0],
        round_trips=[_round_trip(p) for p in pnls],
    )


def test_max_drawdown_hand_computed() -> None:
    # peak 120 then trough 90 -> 0.25 drawdown.
    assert max_drawdown(_equity([100, 120, 90, 110])) == pytest.approx(0.25)


def test_max_drawdown_monotonic_is_zero() -> None:
    assert max_drawdown(_equity([100, 110, 120])) == pytest.approx(0.0)


def test_metrics_hand_computed() -> None:
    # pnls: +100, +30, -50
    m = compute_metrics(_result([1000, 1080], [100, 30, -50]))
    assert m.n_trades == 3
    assert m.win_rate == pytest.approx(2 / 3)
    assert m.profit_factor == pytest.approx(130 / 50)  # 2.6
    assert m.expectancy == pytest.approx(80 / 3)
    assert m.avg_win == pytest.approx(65.0)
    assert m.avg_loss == pytest.approx(-50.0)
    assert m.max_consecutive_wins == 2
    assert m.max_consecutive_losses == 1
    assert m.net_profit == pytest.approx(80.0)


def test_profit_factor_infinite_without_losses() -> None:
    m = compute_metrics(_result([1000, 1130], [100, 30]))
    assert m.profit_factor == math.inf


def test_metrics_no_trades() -> None:
    m = compute_metrics(_result([1000, 1000], []))
    assert m.n_trades == 0
    assert m.win_rate is None
    assert m.profit_factor is None
    assert m.expectancy is None


def test_sharpe_none_on_flat_equity() -> None:
    assert sharpe_ratio(_equity([1000, 1000, 1000, 1000])) is None


def test_sharpe_positive_on_rising_equity() -> None:
    s = sharpe_ratio(_equity([100, 101, 102, 103, 104, 105]))
    assert s is not None and s > 0


def test_monthly_returns() -> None:
    idx = pd.date_range("2024-01-01", periods=70, freq="D", tz="UTC")
    eq = pd.Series(range(100, 170), index=idx, name="equity").astype(float)
    mr = monthly_returns(eq)
    assert len(mr) >= 1
    assert (mr > 0).all()  # strictly increasing equity


def test_integration_metrics_from_backtest() -> None:
    df = generate_ohlcv(rows=200, seed=42)
    result = backtest_strategy(df, BuyAndHold())
    m = compute_metrics(result)
    assert m.n_trades == len(result.round_trips)
    assert m.total_return == pytest.approx(result.total_return)
    assert m.max_drawdown >= 0.0
