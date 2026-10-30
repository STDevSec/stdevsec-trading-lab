"""Paper-trading endpoints (simulation only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from stdevsec_api.api.v1.deps import Pagination, pagination
from stdevsec_api.db.session import get_db
from stdevsec_api.schemas import (
    Page,
    PaperAccountCreate,
    PaperAccountDetailOut,
    PaperAccountOut,
    PaperOrderCreate,
    PaperOrderOut,
    PriceOut,
)
from stdevsec_api.services import market
from stdevsec_api.services import paper as svc

router = APIRouter(prefix="/paper", tags=["paper"])


@router.get("/price", response_model=PriceOut)
def get_price(symbol: str = Query(..., min_length=2, max_length=20)) -> PriceOut:
    """Live spot price from Binance (public, no key). Simulation only."""
    sym = market.validate_symbol(symbol)
    return PriceOut(symbol=sym, price=market.fetch_price(sym))


@router.post("/accounts", response_model=PaperAccountOut, status_code=status.HTTP_201_CREATED)
def create_account(payload: PaperAccountCreate, db: Session = Depends(get_db)) -> PaperAccountOut:
    return PaperAccountOut.model_validate(svc.create_account(db, payload))


@router.get("/accounts", response_model=Page[PaperAccountOut])
def list_accounts(
    page: Pagination = Depends(pagination), db: Session = Depends(get_db)
) -> Page[PaperAccountOut]:
    items, total = svc.list_accounts(db, limit=page.limit, offset=page.offset)
    return Page[PaperAccountOut](
        items=[PaperAccountOut.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/accounts/{account_id}", response_model=PaperAccountDetailOut)
def get_account(account_id: str, db: Session = Depends(get_db)) -> PaperAccountDetailOut:
    return PaperAccountDetailOut.model_validate(svc.get_account(db, account_id))


@router.post(
    "/accounts/{account_id}/orders",
    response_model=PaperOrderOut,
    status_code=status.HTTP_201_CREATED,
)
def place_order(
    account_id: str, payload: PaperOrderCreate, db: Session = Depends(get_db)
) -> PaperOrderOut:
    return PaperOrderOut.model_validate(svc.place_order(db, account_id, payload))


@router.get("/accounts/{account_id}/orders", response_model=Page[PaperOrderOut])
def list_orders(
    account_id: str, page: Pagination = Depends(pagination), db: Session = Depends(get_db)
) -> Page[PaperOrderOut]:
    items, total = svc.list_orders(db, account_id, limit=page.limit, offset=page.offset)
    return Page[PaperOrderOut](
        items=[PaperOrderOut.model_validate(i) for i in items],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )
