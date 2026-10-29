"""OHLCV dataset validation.

Reports data-quality problems in historical candle data. It **never repairs or
silently drops** data: it only describes what it found, so the caller decides.

A dataset is considered valid when it has no ``ERROR``-severity issues.
``WARNING`` issues (e.g. zero-volume candles) do not by themselves invalidate it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

import pandas as pd
from pandas.api import types as ptypes

#: Columns every OHLCV dataset must contain.
REQUIRED_COLUMNS: tuple[str, ...] = ("timestamp", "open", "high", "low", "close", "volume")
#: Price columns, validated for positivity and finiteness.
PRICE_COLUMNS: tuple[str, ...] = ("open", "high", "low", "close")


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    """A single data-quality finding.

    ``rows`` holds a *sample* of affected 0-based positional row indices (not the
    full list) to keep reports bounded; ``count`` is the true number affected.
    """

    code: str
    severity: Severity
    message: str
    count: int = 0
    rows: tuple[int, ...] = ()


@dataclass
class ValidationReport:
    n_rows: int = 0
    issues: list[Issue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity is Severity.ERROR for i in self.issues)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity is Severity.WARNING]

    def _add(
        self,
        code: str,
        severity: Severity,
        message: str,
        *,
        count: int = 0,
        rows: tuple[int, ...] = (),
    ) -> None:
        self.issues.append(Issue(code, severity, message, count=count, rows=rows))


def _sample_positions(mask: pd.Series, limit: int) -> tuple[int, ...]:
    """Return up to ``limit`` 0-based positional indices where ``mask`` is True."""
    positions = [i for i, flag in enumerate(mask.to_numpy().tolist()) if flag]
    return tuple(positions[:limit])


def validate_ohlcv(df: pd.DataFrame, *, sample: int = 5) -> ValidationReport:
    """Validate an OHLCV ``DataFrame`` and return a structured report.

    Checks: required columns, timezone-aware & ordered timestamps, duplicate
    timestamps, missing values, non-positive/non-finite prices, negative volume,
    and high/low consistency. Input is treated as untrusted and never mutated.
    """
    report = ValidationReport(n_rows=int(len(df)))

    # --- 1. Required columns -------------------------------------------------
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        report._add(
            "missing_columns",
            Severity.ERROR,
            f"Missing required columns: {', '.join(missing)}",
            count=len(missing),
        )
        # Without the columns the remaining checks are meaningless.
        return report

    if len(df) == 0:
        report._add("empty_dataset", Severity.ERROR, "Dataset has no rows.")
        return report

    ts = df["timestamp"]

    # --- 2. Timestamp dtype / timezone --------------------------------------
    if not ptypes.is_datetime64_any_dtype(ts):
        report._add(
            "timestamp_not_datetime",
            Severity.ERROR,
            "Column 'timestamp' is not a datetime dtype.",
        )
    elif ptypes.is_datetime64_dtype(ts):
        # datetime64 without tz == naive.
        report._add(
            "timestamp_not_tz_aware",
            Severity.ERROR,
            "Timestamps must be timezone-aware (e.g. UTC); found naive timestamps.",
        )

    # --- 3. Missing values ---------------------------------------------------
    for col in REQUIRED_COLUMNS:
        na = df[col].isna()
        n = int(na.sum())
        if n:
            report._add(
                "missing_values",
                Severity.ERROR,
                f"Column '{col}' has {n} missing value(s).",
                count=n,
                rows=_sample_positions(na, sample),
            )

    # --- 4. Timestamp ordering & duplicates ---------------------------------
    if ptypes.is_datetime64_any_dtype(ts):
        dup = ts.duplicated(keep=False)
        n_dup = int(dup.sum())
        if n_dup:
            report._add(
                "duplicate_timestamps",
                Severity.ERROR,
                f"{n_dup} row(s) share a duplicated timestamp.",
                count=n_dup,
                rows=_sample_positions(dup, sample),
            )
        # strictly increasing (after the NA check above; NaT compares False)
        not_increasing = ts.diff() <= pd.Timedelta(0)
        not_increasing.iloc[0] = False  # first row has no predecessor
        n_ord = int(not_increasing.sum())
        if n_ord:
            report._add(
                "timestamps_not_increasing",
                Severity.ERROR,
                f"{n_ord} timestamp(s) are not strictly after the previous row.",
                count=n_ord,
                rows=_sample_positions(not_increasing, sample),
            )

    # --- 5. Prices: positive & finite ---------------------------------------
    for col in PRICE_COLUMNS:
        if not ptypes.is_numeric_dtype(df[col]):
            report._add(
                "price_not_numeric",
                Severity.ERROR,
                f"Price column '{col}' is not numeric.",
            )
            continue
        bad = ~df[col].apply(lambda v: pd.notna(v) and float("-inf") < v and v > 0)
        n = int(bad.sum())
        if n:
            report._add(
                "invalid_price",
                Severity.ERROR,
                f"Column '{col}' has {n} non-positive or non-finite value(s).",
                count=n,
                rows=_sample_positions(bad, sample),
            )

    # --- 6. Volume: non-negative --------------------------------------------
    if ptypes.is_numeric_dtype(df["volume"]):
        neg = df["volume"] < 0
        n = int(neg.sum())
        if n:
            report._add(
                "negative_volume",
                Severity.ERROR,
                f"{n} row(s) have negative volume.",
                count=n,
                rows=_sample_positions(neg, sample),
            )
        zero = df["volume"] == 0
        n_zero = int(zero.sum())
        if n_zero:
            report._add(
                "zero_volume",
                Severity.WARNING,
                f"{n_zero} candle(s) have zero volume (illiquid or synthetic?).",
                count=n_zero,
                rows=_sample_positions(zero, sample),
            )
    else:
        report._add("volume_not_numeric", Severity.ERROR, "Column 'volume' is not numeric.")

    # --- 7. High/low consistency --------------------------------------------
    if all(ptypes.is_numeric_dtype(df[c]) for c in PRICE_COLUMNS):
        row_max = df[["open", "close", "low"]].max(axis=1)
        row_min = df[["open", "close", "high"]].min(axis=1)
        inconsistent = (df["high"] < row_max) | (df["low"] > row_min) | (df["high"] < df["low"])
        inconsistent = inconsistent.fillna(False)
        n = int(inconsistent.sum())
        if n:
            report._add(
                "high_low_inconsistent",
                Severity.ERROR,
                f"{n} candle(s) violate high>=max(o,c,l), low<=min(o,c,h), high>=low.",
                count=n,
                rows=_sample_positions(inconsistent, sample),
            )

    return report
