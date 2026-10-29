"""Dataset endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from stdevsec_api.api.v1.deps import Pagination, pagination
from stdevsec_api.db.session import get_db
from stdevsec_api.schemas import (
    DatasetCreate,
    DatasetDetailOut,
    DatasetOut,
    OhlcvOut,
    Page,
    ValidationReportOut,
)
from stdevsec_api.services import datasets as svc
from stdevsec_api.services import indicators as ind_svc

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> DatasetOut:
    return DatasetOut.model_validate(svc.create_dataset(db, payload))


@router.post("/upload", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    timeframe: str = Form(...),
    symbol: str | None = Form(None),
    db: Session = Depends(get_db),
) -> DatasetOut:
    """Create a dataset from an uploaded OHLCV CSV.

    CSV columns: timestamp, open, high, low, close, volume.
    """
    data = await file.read()
    return DatasetOut.model_validate(
        svc.create_dataset_from_csv(db, name=name, symbol=symbol, timeframe=timeframe, data=data)
    )


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


@router.get("/{dataset_id}/ohlcv", response_model=OhlcvOut)
def get_ohlcv(dataset_id: str, db: Session = Depends(get_db)) -> OhlcvOut:
    """Candles + a fixed bundle of indicators (SMA/EMA/Bollinger/RSI/MACD)."""
    return OhlcvOut.model_validate(ind_svc.ohlcv_with_indicators(db, dataset_id))
