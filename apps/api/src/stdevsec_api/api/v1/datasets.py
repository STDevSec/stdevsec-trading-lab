"""Dataset endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from stdevsec_api.api.v1.deps import Pagination, pagination
from stdevsec_api.db.session import get_db
from stdevsec_api.schemas import (
    DatasetCreate,
    DatasetDetailOut,
    DatasetOut,
    Page,
    ValidationReportOut,
)
from stdevsec_api.services import datasets as svc

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> DatasetOut:
    return DatasetOut.model_validate(svc.create_dataset(db, payload))


@router.get("", response_model=Page[DatasetOut])
def list_datasets(
    page: Pagination = Depends(pagination), db: Session = Depends(get_db)
) -> Page[DatasetOut]:
    items, total = svc.list_datasets(db, limit=page.limit, offset=page.offset)
    return Page[DatasetOut](
        items=[DatasetOut.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{dataset_id}", response_model=DatasetDetailOut)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)) -> DatasetDetailOut:
    return DatasetDetailOut.model_validate(svc.get_dataset(db, dataset_id))


@router.post("/{dataset_id}/validate", response_model=ValidationReportOut)
def validate_dataset(dataset_id: str, db: Session = Depends(get_db)) -> ValidationReportOut:
    return ValidationReportOut.model_validate(svc.revalidate_latest(db, dataset_id))
