"""Dataset service: create (validate + store), list, fetch, re-validate."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from quant_engine import validate_ohlcv
from stdevsec_api.db.models import Dataset, DatasetVersion
from stdevsec_api.errors import DomainValidationError, NotFoundError
from stdevsec_api.schemas import DatasetCreate
from stdevsec_api.services.ohlcv import (
    candles_from_models,
    candles_to_df,
    candles_to_storage,
    report_to_dict,
)


def create_dataset(db: Session, payload: DatasetCreate) -> Dataset:
    """Validate the candles and, only if valid, persist dataset + version 1."""
    df = candles_from_models(payload.candles)
    report = validate_ohlcv(df)
    if not report.is_valid:
        raise DomainValidationError(
            "Dataset failed OHLCV validation", details=report_to_dict(report)
        )

    dataset = Dataset(name=payload.name, symbol=payload.symbol, timeframe=payload.timeframe)
    dataset.versions.append(
        DatasetVersion(
            version=1,
            n_rows=report.n_rows,
            is_valid=True,
            validation=report_to_dict(report),
            candles=candles_to_storage(payload.candles),
        )
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def list_datasets(db: Session, *, limit: int, offset: int) -> tuple[list[Dataset], int]:
    total = db.scalar(select(func.count()).select_from(Dataset)) or 0
    items = db.scalars(
        select(Dataset).order_by(Dataset.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), total


def get_dataset(db: Session, dataset_id: str) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise NotFoundError(f"Dataset '{dataset_id}' not found")
    return dataset


def latest_version(dataset: Dataset) -> DatasetVersion:
    if not dataset.versions:
        raise NotFoundError(f"Dataset '{dataset.id}' has no versions")
    return dataset.versions[-1]  # versions are ordered by version ascending


def revalidate_latest(db: Session, dataset_id: str) -> dict[str, Any]:
    dataset = get_dataset(db, dataset_id)
    version = latest_version(dataset)
    report = validate_ohlcv(candles_to_df(version.candles))
    return report_to_dict(report)
