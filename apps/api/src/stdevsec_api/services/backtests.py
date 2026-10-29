"""Backtest service: run via the quant-engine and persist the result."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from quant_engine import backtest_strategy, compute_metrics
from stdevsec_api.db.models import BacktestRun, BacktestTrade, EquitySnapshot
from stdevsec_api.errors import NotFoundError
from stdevsec_api.schemas import BacktestCreate
from stdevsec_api.services.datasets import get_dataset, latest_version
from stdevsec_api.services.ohlcv import candles_to_df, metrics_to_json
from stdevsec_api.services.strategies import build_strategy


def run_backtest(db: Session, payload: BacktestCreate) -> BacktestRun:
    dataset = get_dataset(db, payload.dataset_id)
    version = latest_version(dataset)
    df = candles_to_df(version.candles)
    strategy = build_strategy(payload.strategy, payload.params)

    result = backtest_strategy(
        df,
        strategy,
        capital=payload.initial_capital,
        commission_bps=payload.commission_bps,
        slippage_bps=payload.slippage_bps,
        max_drawdown_halt=payload.max_drawdown_halt,
    )
    metrics = compute_metrics(result)

    run = BacktestRun(
        dataset_version_id=version.id,
        strategy_name=payload.strategy,
        params=payload.params,
        initial_capital=payload.initial_capital,
        commission_bps=payload.commission_bps,
        slippage_bps=payload.slippage_bps,
        max_drawdown_halt=payload.max_drawdown_halt,
        status="completed",
        final_equity=result.final_equity,
        total_return=result.total_return,
        metrics=metrics_to_json(metrics),
    )
    for rt in result.round_trips:
        run.trades.append(
            BacktestTrade(
                entry_time=rt.entry_time.to_pydatetime(),
                exit_time=rt.exit_time.to_pydatetime(),
                units=rt.units,
                entry_price=rt.entry_price,
                exit_price=rt.exit_price,
                pnl=rt.pnl,
                return_pct=rt.return_pct,
            )
        )
    for timestamp, equity in result.equity.items():
        run.equity_snapshots.append(
            EquitySnapshot(timestamp=timestamp.to_pydatetime(), equity=float(equity))
        )

    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def get_run(db: Session, run_id: str) -> BacktestRun:
    run = db.get(BacktestRun, run_id)
    if run is None:
        raise NotFoundError(f"Backtest run '{run_id}' not found")
    return run


def list_runs(db: Session, *, limit: int, offset: int) -> tuple[list[BacktestRun], int]:
    total = db.scalar(select(func.count()).select_from(BacktestRun)) or 0
    items = db.scalars(
        select(BacktestRun).order_by(BacktestRun.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), total


def list_equity(db: Session, run_id: str) -> list[EquitySnapshot]:
    """Full equity curve for a run, ordered by time.

    Returned whole (not paginated): a chart needs the complete series. Bounded
    by the dataset size cap (``max_candles``), so one point per bar stays sane.
    """
    get_run(db, run_id)  # 404 if the run does not exist
    return list(
        db.scalars(
            select(EquitySnapshot)
            .where(EquitySnapshot.run_id == run_id)
            .order_by(EquitySnapshot.timestamp)
        ).all()
    )


def list_trades(
    db: Session, run_id: str, *, limit: int, offset: int
) -> tuple[list[BacktestTrade], int]:
    get_run(db, run_id)  # 404 if the run does not exist
    total = (
        db.scalar(
            select(func.count()).select_from(BacktestTrade).where(BacktestTrade.run_id == run_id)
        )
        or 0
    )
    items = db.scalars(
        select(BacktestTrade)
        .where(BacktestTrade.run_id == run_id)
        .order_by(BacktestTrade.entry_time)
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total
