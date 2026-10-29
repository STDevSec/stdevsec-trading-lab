from __future__ import annotations

import pandas as pd
import pytest

from quant_engine.backtest import run_backtest


def make_df(opens: list[float], closes: list[float]) -> pd.DataFrame:
    n = len(opens)
    ts = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame(
        {
            "timestamp": ts,
            "open": opens,
            "high": [max(o, c) for o, c in zip(opens, closes, strict=True)],
            "low": [min(o, c) for o, c in zip(opens, closes, strict=True)],
            "close": closes,
            "volume": [1] * n,
        }
    )


def test_golden_buy_and_hold_no_costs() -> None:
    # Hand-computed: capital 1000, enter 10 units @ open[1]=100, hold.
    df = make_df(opens=[100, 100, 110], closes=[100, 110, 121])
    signals = pd.Series([1.0, 1.0, 1.0], index=df.index)

    result = run_backtest(df, signals, capital=1000.0)

    assert list(result.equity) == pytest.approx([1000.0, 1100.0, 1210.0])
    assert result.total_return == pytest.approx(0.21)
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.side == "buy"
    assert trade.units == pytest.approx(10.0)
    assert trade.price == pytest.approx(100.0)


def test_flat_strategy_never_trades() -> None:
    df = make_df(opens=[100, 105, 110], closes=[101, 106, 111])
    signals = pd.Series([0.0, 0.0, 0.0], index=df.index)

    result = run_backtest(df, signals, capital=500.0)

    assert result.trades == []
    assert list(result.equity) == pytest.approx([500.0, 500.0, 500.0])


def test_no_lookahead_last_signal_has_no_effect() -> None:
    # The final bar's signal would only execute at a (nonexistent) next bar,
    # so flipping it must not change trades or equity.
    df = make_df(opens=[100, 100, 110, 120], closes=[100, 110, 121, 130])
    base = pd.Series([1.0, 1.0, 1.0, 0.0], index=df.index)
    flipped = pd.Series([1.0, 1.0, 1.0, 1.0], index=df.index)

    r1 = run_backtest(df, base, capital=1000.0)
    r2 = run_backtest(df, flipped, capital=1000.0)

    assert list(r1.equity) == pytest.approx(list(r2.equity))
    assert len(r1.trades) == len(r2.trades)


def test_commission_reduces_equity() -> None:
    df = make_df(opens=[100, 100, 110], closes=[100, 110, 121])
    signals = pd.Series([1.0, 1.0, 1.0], index=df.index)

    free = run_backtest(df, signals, capital=1000.0)
    costed = run_backtest(df, signals, capital=1000.0, commission_bps=10.0)

    assert costed.final_equity < free.final_equity


def test_slippage_reduces_equity() -> None:
    df = make_df(opens=[100, 100, 110], closes=[100, 110, 121])
    signals = pd.Series([1.0, 1.0, 1.0], index=df.index)

    free = run_backtest(df, signals, capital=1000.0)
    slipped = run_backtest(df, signals, capital=1000.0, slippage_bps=50.0)

    assert slipped.final_equity < free.final_equity


def test_is_deterministic() -> None:
    df = make_df(opens=[100, 102, 101, 105], closes=[101, 101, 104, 106])
    signals = pd.Series([1.0, 0.0, 1.0, 1.0], index=df.index)

    a = run_backtest(df, signals, capital=1000.0, commission_bps=5.0, slippage_bps=5.0)
    b = run_backtest(df, signals, capital=1000.0, commission_bps=5.0, slippage_bps=5.0)

    assert list(a.equity) == pytest.approx(list(b.equity))


def test_rejects_nonpositive_capital() -> None:
    df = make_df(opens=[100, 100], closes=[100, 110])
    with pytest.raises(ValueError):
        run_backtest(df, pd.Series([1.0, 1.0], index=df.index), capital=0.0)
