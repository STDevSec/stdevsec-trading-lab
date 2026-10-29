"""STDevsec Trading Lab — deterministic quantitative engine."""

from quant_engine.analytics import (
    Metrics,
    compute_metrics,
    max_drawdown,
    monthly_returns,
    sharpe_ratio,
)
from quant_engine.backtest import (
    BacktestResult,
    RoundTrip,
    Trade,
    backtest_strategy,
    run_backtest,
)
from quant_engine.risk import position_size_from_risk, risk_reward_ratio
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
    "Metrics",
    "RoundTrip",
    "SMACrossover",
    "Severity",
    "Strategy",
    "Trade",
    "ValidationReport",
    "backtest_strategy",
    "compute_metrics",
    "generate_ohlcv",
    "max_drawdown",
    "monthly_returns",
    "position_size_from_risk",
    "risk_reward_ratio",
    "run_backtest",
    "sharpe_ratio",
    "validate_ohlcv",
]

__version__ = "0.1.0"
