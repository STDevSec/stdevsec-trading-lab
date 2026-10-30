"""ORM models for the backtest persistence slice.

Cross-dialect on purpose (``String``/``JSON``/``Float``): Postgres in production,
SQLite in tests. Deferred entities (User, Workspace, Instrument, Strategy,
TradingJournalEntry, LearningProgress, AuditEvent) arrive in later sprints — see
ADR-0007.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stdevsec_api.db.base import Base


def _uuid() -> str:
    return uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    symbol: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timeframe: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    versions: Mapped[list["DatasetVersion"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="DatasetVersion.version",
    )


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (UniqueConstraint("dataset_id", "version", name="uq_dataset_version"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    n_rows: Mapped[int] = mapped_column(Integer)
    is_valid: Mapped[bool] = mapped_column(Boolean)
    validation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    candles: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    dataset: Mapped["Dataset"] = relationship(back_populates="versions")


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    dataset_version_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"), index=True
    )
    strategy_name: Mapped[str] = mapped_column(String(64))
    params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    initial_capital: Mapped[float] = mapped_column(Float)
    commission_bps: Mapped[float] = mapped_column(Float, default=0.0)
    slippage_bps: Mapped[float] = mapped_column(Float, default=0.0)
    max_drawdown_halt: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="completed")
    final_equity: Mapped[float] = mapped_column(Float)
    total_return: Mapped[float] = mapped_column(Float)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    trades: Mapped[list["BacktestTrade"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    equity_snapshots: Mapped[list["EquitySnapshot"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EquitySnapshot.timestamp",
    )


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("backtest_runs.id", ondelete="CASCADE"), index=True
    )
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    exit_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    units: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float] = mapped_column(Float)
    pnl: Mapped[float] = mapped_column(Float)
    return_pct: Mapped[float] = mapped_column(Float)

    run: Mapped["BacktestRun"] = relationship(back_populates="trades")


class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("backtest_runs.id", ondelete="CASCADE"), index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    equity: Mapped[float] = mapped_column(Float)

    run: Mapped["BacktestRun"] = relationship(back_populates="equity_snapshots")


class JournalEntry(Base):
    """A trading-journal note: free text + tags + optional screenshots.

    May reference a backtest run; if that run is deleted the link is cleared
    (SET NULL) so the note survives.
    """

    __tablename__ = "journal_entries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    run_id: Mapped[str | None] = mapped_column(
        ForeignKey("backtest_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    images: Mapped[list["JournalImage"]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="JournalImage.created_at",
    )


class JournalImage(Base):
    """A screenshot attached to a journal entry (bytes stored in the DB).

    ponytail: DB blob, capped per-image; move to object storage if the journal
    grows large.
    """

    __tablename__ = "journal_images"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    entry_id: Mapped[str] = mapped_column(
        ForeignKey("journal_entries.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    data: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    entry: Mapped["JournalEntry"] = relationship(back_populates="images")


class PaperAccount(Base):
    """A simulated trading account: cash + long-only positions. No real money."""

    __tablename__ = "paper_accounts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120))
    cash: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    positions: Mapped[list["PaperPosition"]] = relationship(
        back_populates="account", cascade="all, delete-orphan", order_by="PaperPosition.symbol"
    )
    orders: Mapped[list["PaperOrder"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class PaperPosition(Base):
    """Net long position per symbol (no shorting / leverage in the MVP)."""

    __tablename__ = "paper_positions"
    __table_args__ = (UniqueConstraint("account_id", "symbol", name="uq_paper_position"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(20))
    qty: Mapped[float] = mapped_column(Float)
    avg_price: Mapped[float] = mapped_column(Float)

    account: Mapped["PaperAccount"] = relationship(back_populates="positions")


class PaperOrder(Base):
    """An executed simulated order (market fill at the provided price)."""

    __tablename__ = "paper_orders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(20))
    side: Mapped[str] = mapped_column(String(4))  # "buy" | "sell"
    qty: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    account: Mapped["PaperAccount"] = relationship(back_populates="orders")
