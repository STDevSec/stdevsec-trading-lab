"""Trading-journal endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from stdevsec_api.api.v1.deps import Pagination, pagination
from stdevsec_api.db.session import get_db
from stdevsec_api.schemas import (
    JournalEntryCreate,
    JournalEntryDetailOut,
    JournalEntryOut,
    JournalEntryUpdate,
    JournalImageOut,
    Page,
)
from stdevsec_api.services import journal as svc

router = APIRouter(prefix="/journal", tags=["journal"])


@router.post("/entries", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(payload: JournalEntryCreate, db: Session = Depends(get_db)) -> JournalEntryOut:
    return JournalEntryOut.model_validate(svc.create_entry(db, payload))


@router.get("/entries", response_model=Page[JournalEntryOut])
def list_entries(
    page: Pagination = Depends(pagination), db: Session = Depends(get_db)
) -> Page[JournalEntryOut]:
    items, total = svc.list_entries(db, limit=page.limit, offset=page.offset)
    return Page[JournalEntryOut](
        items=[JournalEntryOut.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/entries/{entry_id}", response_model=JournalEntryDetailOut)
def get_entry(entry_id: str, db: Session = Depends(get_db)) -> JournalEntryDetailOut:
    return JournalEntryDetailOut.model_validate(svc.get_entry(db, entry_id))


@router.patch("/entries/{entry_id}", response_model=JournalEntryOut)
def update_entry(
    entry_id: str, payload: JournalEntryUpdate, db: Session = Depends(get_db)
) -> JournalEntryOut:
    return JournalEntryOut.model_validate(svc.update_entry(db, entry_id, payload))


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(entry_id: str, db: Session = Depends(get_db)) -> Response:
    svc.delete_entry(db, entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/entries/{entry_id}/images",
    response_model=JournalImageOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_image(
    entry_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> JournalImageOut:
    data = await file.read()
    image = svc.add_image(
        db,
        entry_id,
        filename=file.filename or "screenshot",
        content_type=file.content_type or "application/octet-stream",
        data=data,
    )
    return JournalImageOut.model_validate(image)


@router.get("/entries/{entry_id}/images/{image_id}")
def get_image(entry_id: str, image_id: str, db: Session = Depends(get_db)) -> Response:
    image = svc.get_image(db, entry_id, image_id)
    return Response(content=image.data, media_type=image.content_type)
