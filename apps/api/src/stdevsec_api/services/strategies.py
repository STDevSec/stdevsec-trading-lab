"""Built-in strategy catalog and factory.

The API exposes the engine's strategies by name + params; there is no Strategy
DB table yet (deferred, ADR-0007). A backtest stores its strategy name and params
inline.
"""

from __future__ import annotations

from typing import Any

from quant_engine import BuyAndHold, SMACrossover, Strategy
from stdevsec_api.errors import DomainValidationError
from stdevsec_api.schemas import StrategyInfo, StrategyParam

CATALOG: list[StrategyInfo] = [
    StrategyInfo(
        name="buy_and_hold",
        description="Siempre totalmente invertido; entra en la primera barra ejecutable.",
        params=[],
    ),
    StrategyInfo(
        name="sma_crossover",
        description="Largo mientras la SMA rápida está por encima de la lenta.",
        params=[
            StrategyParam(name="fast", type="int", default=10, description="Ventana SMA rápida"),
            StrategyParam(name="slow", type="int", default=30, description="Ventana SMA lenta"),
        ],
    ),
]


def build_strategy(name: str, params: dict[str, Any]) -> Strategy:
    if name == "buy_and_hold":
        return BuyAndHold()
    if name == "sma_crossover":
        try:
            fast = int(params.get("fast", 10))
            slow = int(params.get("slow", 30))
            return SMACrossover(fast=fast, slow=slow)
        except (ValueError, TypeError) as exc:
            raise DomainValidationError(f"Invalid sma_crossover params: {exc}") from exc
    raise DomainValidationError(
        f"Unknown strategy '{name}'",
        details={"available": [s.name for s in CATALOG]},
    )
