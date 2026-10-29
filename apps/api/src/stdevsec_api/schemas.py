"""Request/response schemas (Pydantic v2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Page(BaseModel, Generic[T]):  # noqa: UP046  (keep explicit Generic for pydantic)
    items: list[T]
    total: int
    limit: int
    offset: int


# --- Datasets ---------------------------------------------------------------
class CandleIn(BaseModel):
    timestamp: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)


class DatasetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    symbol: str | None = Field(default=None, max_length=64)
    timeframe: str = Field(min_length=1, max_length=16)
    candles: list[CandleIn] = Field(min_length=1)


class ValidationIssueOut(BaseModel):
    code: str
    severity: str
    message: str
    count: int


class ValidationReportOut(BaseModel):
    is_valid: bool
    n_rows: int
    issues: list[ValidationIssueOut]


class DatasetVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: int
    n_rows: int
    is_valid: bool
    created_at: datetime


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    symbol: str | None
    timeframe: str
    created_at: datetime


class DatasetDetailOut(DatasetOut):
    versions: list[DatasetVersionOut]


class OhlcvCandle(BaseModel):
    time: int  # unix seconds (UTC), for lightweight-charts
    open: float
    high: float
    low: float
    close: float
    volume: float


class OhlcvOut(BaseModel):
    """A dataset's candles plus a fixed bundle of technical indicators.

    Each indicator series is index-aligned with ``candles``; warm-up / undefined
    points are ``null`` (NaN is never serialized).
    """

    candles: list[OhlcvCandle]
    indicators: dict[str, list[float | None]]


# --- Strategies -------------------------------------------------------------
class StrategyParam(BaseModel):
    name: str
    type: str
    default: Any
    description: str


class StrategyInfo(BaseModel):
    name: str
    description: str
    params: list[StrategyParam]


# --- Backtests --------------------------------------------------------------
class BacktestCreate(BaseModel):
    dataset_id: str
    strategy: str
    params: dict[str, Any] = Field(default_factory=dict)
    initial_capital: float = Field(default=10_000.0, gt=0)
    commission_bps: float = Field(default=0.0, ge=0)
    slippage_bps: float = Field(default=0.0, ge=0)
    max_drawdown_halt: float | None = Field(default=None, gt=0, le=1)


class MetricsOut(BaseModel):
    n_trades: int
    win_rate: float | None
    profit_factor: float | None
    expectancy: float | None
    avg_win: float | None
    avg_loss: float | None
    net_profit: float
    total_return: float
    max_drawdown: float
    sharpe: float | None
    max_consecutive_wins: int
    max_consecutive_losses: int


class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entry_time: datetime
    exit_time: datetime
    units: float
    entry_price: float
    exit_price: float
    pnl: float
    return_pct: float


class EquityPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    equity: float


class BacktestRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dataset_version_id: str
    strategy_name: str
    params: dict[str, Any]
    initial_capital: float
    commission_bps: float
    slippage_bps: float
    max_drawdown_halt: float | None
    status: str
    final_equity: float
    total_return: float
    metrics: dict[str, Any]
    created_at: datetime


# --- Journal ----------------------------------------------------------------
class JournalEntryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = Field(default="", max_length=20_000)
    tags: list[str] = Field(default_factory=list)
    run_id: str | None = None


class JournalImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    created_at: datetime


class JournalEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    notes: str
    tags: list[str]
    run_id: str | None
    created_at: datetime


class JournalEntryDetailOut(JournalEntryOut):
    images: list[JournalImageOut]
