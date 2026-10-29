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
from quant_engine.indicators import bollinger, ema, macd, rsi, sma
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
    "bollinger",
    "compute_metrics",
    "ema",
    "generate_ohlcv",
    "macd",
    "max_drawdown",
    "monthly_returns",
    "position_size_from_risk",
    "risk_reward_ratio",
    "rsi",
    "run_backtest",
    "sharpe_ratio",
    "sma",
    "validate_ohlcv",
]

__version__ = "0.1.0"
