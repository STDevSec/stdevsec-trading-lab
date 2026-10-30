"""Trading-journal service: entries (CRUD) + screenshot attachments."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from stdevsec_api.config import get_settings
from stdevsec_api.db.models import JournalEntry, JournalImage
from stdevsec_api.errors import DomainValidationError, NotFoundError, PayloadTooLargeError
from stdevsec_api.schemas import JournalEntryCreate, JournalEntryUpdate


def create_entry(db: Session, payload: JournalEntryCreate) -> JournalEntry:
    entry = JournalEntry(
        title=payload.title,
        notes=payload.notes,
        tags=[t.strip() for t in payload.tags if t.strip()],
        run_id=payload.run_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_entries(db: Session, *, limit: int, offset: int) -> tuple[list[JournalEntry], int]:
    total = db.scalar(select(func.count()).select_from(JournalEntry)) or 0
    items = db.scalars(
        select(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), total


def get_entry(db: Session, entry_id: str) -> JournalEntry:
    entry = db.get(JournalEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"Journal entry '{entry_id}' not found")
    return entry


def update_entry(db: Session, entry_id: str, payload: JournalEntryUpdate) -> JournalEntry:
    entry = get_entry(db, entry_id)
    if payload.notes is not None:
        entry.notes = payload.notes
    if payload.tags is not None:
        entry.tags = [t.strip() for t in payload.tags if t.strip()]
    db.commit()
    db.refresh(entry)
    return entry


def delete_entry(db: Session, entry_id: str) -> None:
    db.delete(get_entry(db, entry_id))  # cascade removes its images
    db.commit()


def add_image(
    db: Session, entry_id: str, *, filename: str, content_type: str, data: bytes
) -> JournalImage:
    entry = get_entry(db, entry_id)
    if not content_type.startswith("image/"):
        raise DomainValidationError(f"Not an image: {content_type!r}")
    cap = get_settings().max_upload_bytes
    if len(data) > cap:
        raise PayloadTooLargeError(f"Image is {len(data)} bytes, exceeds cap of {cap}.")
    image = JournalImage(
        entry_id=entry.id, filename=filename, content_type=content_type, data=data
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def get_image(db: Session, entry_id: str, image_id: str) -> JournalImage:
    image = db.get(JournalImage, image_id)
    if image is None or image.entry_id != entry_id:
        raise NotFoundError(f"Image '{image_id}' not found")
    return image
