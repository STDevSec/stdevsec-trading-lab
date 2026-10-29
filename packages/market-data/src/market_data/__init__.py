"""STDevsec Trading Lab — market-data IO (untrusted input is treated as such)."""

from market_data.io import (
    DEFAULT_MAX_BYTES,
    DatasetTooLargeError,
    neutralize_csv_value,
    read_ohlcv_csv,
    read_ohlcv_csv_bytes,
    safe_resolve,
    write_ohlcv_csv,
)

__all__ = [
    "DEFAULT_MAX_BYTES",
    "DatasetTooLargeError",
    "neutralize_csv_value",
    "read_ohlcv_csv",
    "read_ohlcv_csv_bytes",
    "safe_resolve",
    "write_ohlcv_csv",
]

__version__ = "0.1.0"
