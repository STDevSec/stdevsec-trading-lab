"""Backtest endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from stdevsec_api.api.v1.deps import Pagination, pagination
from stdevsec_api.db.session import get_db
from stdevsec_api.schemas import (
    BacktestCreate,
    BacktestRunOut,
    EquityPointOut,
    MetricsOut,
    Page,
    TradeOut,
)
from stdevsec_api.services import backtests as svc

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("", response_model=BacktestRunOut, status_code=status.HTTP_201_CREATED)
def create_backtest(payload: BacktestCreate, db: Session = Depends(get_db)) -> BacktestRunOut:
    return BacktestRunOut.model_validate(svc.run_backtest(db, payload))


@router.get("", response_model=Page[BacktestRunOut])
def list_backtests(
    page: Pagination = Depends(pagination), db: Session = Depends(get_db)
) -> Page[BacktestRunOut]:
    items, total = svc.list_runs(db, limit=page.limit, offset=page.offset)
    return Page[BacktestRunOut](
        items=[BacktestRunOut.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{run_id}", response_model=BacktestRunOut)
def get_backtest(run_id: str, db: Session = Depends(get_db)) -> BacktestRunOut:
    return BacktestRunOut.model_validate(svc.get_run(db, run_id))


@router.get("/{run_id}/trades", response_model=Page[TradeOut])
def get_trades(
    run_id: str, page: Pagination = Depends(pagination), db: Session = Depends(get_db)
) -> Page[TradeOut]:
    items, total = svc.list_trades(db, run_id, limit=page.limit, offset=page.offset)
    return Page[TradeOut](
        items=[TradeOut.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{run_id}/equity", response_model=list[EquityPointOut])
def get_equity(run_id: str, db: Session = Depends(get_db)) -> list[EquityPointOut]:
    return [EquityPointOut.model_validate(p) for p in svc.list_equity(db, run_id)]


@router.get("/{run_id}/metrics", response_model=MetricsOut)
def get_metrics(run_id: str, db: Session = Depends(get_db)) -> MetricsOut:
    run = svc.get_run(db, run_id)
    return MetricsOut.model_validate(run.metrics)
