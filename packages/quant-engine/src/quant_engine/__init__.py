"""STDevsec Trading Lab — deterministic quantitative engine."""

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
    "Issue",
    "Severity",
    "ValidationReport",
    "generate_ohlcv",
    "validate_ohlcv",
]

__version__ = "0.1.0"
