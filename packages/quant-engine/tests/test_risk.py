from __future__ import annotations

import pytest

from quant_engine.risk import position_size_from_risk, risk_reward_ratio


def test_position_size_from_risk_basic() -> None:
    # Risk 1% of 10_000 = 100; stop 2 away -> 50 units.
    units = position_size_from_risk(10_000.0, 0.01, entry_price=100.0, stop_price=98.0)
    assert units == pytest.approx(50.0)


def test_position_size_scales_with_risk() -> None:
    small = position_size_from_risk(10_000.0, 0.01, 100.0, 95.0)
    big = position_size_from_risk(10_000.0, 0.02, 100.0, 95.0)
    assert big == pytest.approx(2 * small)


@pytest.mark.parametrize(
    "capital,risk,entry,stop",
    [
        (0.0, 0.01, 100.0, 95.0),  # bad capital
        (10_000.0, 0.0, 100.0, 95.0),  # bad risk
        (10_000.0, 1.5, 100.0, 95.0),  # risk > 1
        (10_000.0, 0.01, 100.0, 100.0),  # entry == stop
        (10_000.0, 0.01, -1.0, 95.0),  # bad price
    ],
)
def test_position_size_validation(capital: float, risk: float, entry: float, stop: float) -> None:
    with pytest.raises(ValueError):
        position_size_from_risk(capital, risk, entry, stop)


def test_risk_reward_ratio() -> None:
    # entry 100, stop 95 (risk 5), target 115 (reward 15) -> 3.0
    assert risk_reward_ratio(100.0, 95.0, 115.0) == pytest.approx(3.0)


def test_risk_reward_requires_distinct_stop() -> None:
    with pytest.raises(ValueError):
        risk_reward_ratio(100.0, 100.0, 115.0)
