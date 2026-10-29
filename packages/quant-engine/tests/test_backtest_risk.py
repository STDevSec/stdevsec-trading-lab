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


def test_round_trip_realized_pnl() -> None:
    # Buy @100 (open[1]), sell @120 (open[3]); 10 units; pnl = 200, no costs.
    df = make_df(opens=[100, 100, 110, 120], closes=[100, 110, 121, 100])
    signals = pd.Series([1.0, 1.0, 0.0, 0.0], index=df.index)

    result = run_backtest(df, signals, capital=1000.0)

    assert len(result.round_trips) == 1
    rt = result.round_trips[0]
    assert rt.entry_price == pytest.approx(100.0)
    assert rt.exit_price == pytest.approx(120.0)
    assert rt.units == pytest.approx(10.0)
    assert rt.pnl == pytest.approx(200.0)
    assert rt.return_pct == pytest.approx(0.2)


def test_open_position_has_no_round_trip() -> None:
    # Still long at the end -> no completed round trip.
    df = make_df(opens=[100, 100, 110], closes=[100, 110, 121])
    signals = pd.Series([1.0, 1.0, 1.0], index=df.index)

    result = run_backtest(df, signals, capital=1000.0)

    assert result.round_trips == []
    assert len(result.trades) == 1  # the entry buy only


def test_max_drawdown_halt_stops_the_bleeding() -> None:
    # Crashing series, fully invested. Halt at 15% drawdown (kept off the exact
    # threshold boundary so the trigger bar is unambiguous).
    df = make_df(opens=[100, 100, 80, 70], closes=[100, 80, 70, 60])
    signals = pd.Series([1.0, 1.0, 1.0, 1.0], index=df.index)

    halted = run_backtest(df, signals, capital=1000.0, max_drawdown_halt=0.15)
    unhalted = run_backtest(df, signals, capital=1000.0)

    # Enter 10 units @100. close[1]=80 -> equity 800 -> -20% dd -> halt.
    # Without halt: 10 * close[3]=60 = 600. With halt: liquidated @open[2]=80 -> 800.
    assert unhalted.final_equity == pytest.approx(600.0)
    assert halted.final_equity == pytest.approx(800.0)
    assert halted.final_equity > unhalted.final_equity
    # Equity is flat once halted (position liquidated).
    assert halted.equity.iloc[-1] == pytest.approx(halted.equity.iloc[-2])


def test_halt_threshold_validation() -> None:
    df = make_df(opens=[100, 100], closes=[100, 90])
    with pytest.raises(ValueError):
        run_backtest(df, pd.Series([1.0, 1.0], index=df.index), max_drawdown_halt=1.5)
