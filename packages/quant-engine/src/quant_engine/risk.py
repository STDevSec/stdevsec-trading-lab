"""Risk-management primitives.

Pure, deterministic helpers for position sizing and risk/reward. The drawdown
halt itself lives in the backtester (it needs running equity); see
``run_backtest(max_drawdown_halt=...)``.

Out of scope for now (single-asset, long/flat MVP): daily loss limits, exposure
across instruments and maximum simultaneous positions — these arrive with the
multi-asset / intraday engine and will be documented in their own ADR.
"""

from __future__ import annotations


def position_size_from_risk(
    capital: float,
    risk_per_trade: float,
    entry_price: float,
    stop_price: float,
) -> float:
    """Units to buy so that hitting the stop loses ``risk_per_trade`` of capital.

    ``risk_per_trade`` is a fraction (e.g. 0.01 for 1%). Formula:
    ``units = capital * risk_per_trade / |entry - stop|``.
    """
    if capital <= 0:
        raise ValueError("capital must be positive")
    if not 0 < risk_per_trade <= 1:
        raise ValueError("risk_per_trade must be in (0, 1]")
    if entry_price <= 0 or stop_price <= 0:
        raise ValueError("prices must be positive")
    per_unit_risk = abs(entry_price - stop_price)
    if per_unit_risk <= 0:
        raise ValueError("entry and stop must differ")
    return capital * risk_per_trade / per_unit_risk


def risk_reward_ratio(entry_price: float, stop_price: float, target_price: float) -> float:
    """Reward-to-risk ratio: ``|target - entry| / |entry - stop|``."""
    risk = abs(entry_price - stop_price)
    if risk <= 0:
        raise ValueError("entry and stop must differ")
    reward = abs(target_price - entry_price)
    return reward / risk
