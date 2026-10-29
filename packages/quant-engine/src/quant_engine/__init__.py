"""STDevsec Trading Lab — deterministic quantitative engine."""

from quant_engine.backtest import (
    BacktestResult,
    Trade,
    backtest_strategy,
    run_backtest,
)
from quant_engine.strategy import BuyAndHold, SMACrossover, Strategy
from quant_engine.synthetic import generate_ohlcv
from quant_engine.validation import (
    PRICE_COLUMNS,
    REQUIRED_COLUMNS,
    Issue,
    Severity,
    ValidationReport,
    validate_ohlcv,
)

__all__ = [
    "PRICE_COLUMNS",
    "REQUIRED_COLUMNS",
    "BacktestResult",
    "BuyAndHold",
    "Issue",
    "SMACrossover",
    "Severity",
    "Strategy",
    "Trade",
    "ValidationReport",
    "backtest_strategy",
    "generate_ohlcv",
    "run_backtest",
    "validate_ohlcv",
]

__version__ = "0.1.0"
