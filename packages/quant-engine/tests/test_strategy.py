from __future__ import annotations

import pandas as pd
import pytest

from quant_engine.backtest import backtest_strategy
from quant_engine.strategy import BuyAndHold, SMACrossover
from quant_engine.synthetic import generate_ohlcv


def _df_from_closes(closes: list[float]) -> pd.DataFrame:
    n = len(closes)
    ts = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1] * n,
        }
    )


def test_buy_and_hold_is_always_long() -> None:
    df = generate_ohlcv(rows=20, seed=1)
    signals = BuyAndHold().generate_signals(df)
    assert (signals == 1.0).all()
    assert signals.index.equals(df.index)


def test_sma_crossover_rejects_bad_windows() -> None:
    with pytest.raises(ValueError):
        SMACrossover(fast=30, slow=10)
    with pytest.raises(ValueError):
        SMACrossover(fast=10, slow=10)
    with pytest.raises(ValueError):
        SMACrossover(fast=0, slow=5)


def test_sma_crossover_flat_during_warmup() -> None:
    df = _df_from_closes([10, 11, 12, 13, 14, 15])
    signals = SMACrossover(fast=2, slow=3).generate_signals(df)
    # First (slow-1)=2 bars have no full slow window -> flat.
    assert signals.iloc[0] == 0.0
    assert signals.iloc[1] == 0.0


def test_sma_crossover_goes_long_on_uptrend() -> None:
    df = _df_from_closes([10, 11, 12, 13, 14, 15, 16, 17])
    signals = SMACrossover(fast=2, slow=3).generate_signals(df)
    # On a steady uptrend the fast MA stays above the slow MA once warmed up.
    assert signals.iloc[-1] == 1.0


def test_backtest_strategy_is_deterministic() -> None:
    df = generate_ohlcv(rows=300, seed=42)
    strat = SMACrossover(fast=10, slow=30)
    a = backtest_strategy(df, strat, capital=10_000.0, commission_bps=5.0)
    b = backtest_strategy(df, strat, capital=10_000.0, commission_bps=5.0)
    assert list(a.equity) == list(b.equity)
    assert len(a.trades) == len(b.trades)


def test_buy_and_hold_matches_price_return() -> None:
    # With no costs, buy-and-hold return equals the open[1]->close[-1] price move.
    df = generate_ohlcv(rows=100, seed=7)
    result = backtest_strategy(df, BuyAndHold(), capital=10_000.0)
    expected = df["close"].iloc[-1] / df["open"].iloc[1] - 1.0
    assert result.total_return == pytest.approx(expected, rel=1e-9)
