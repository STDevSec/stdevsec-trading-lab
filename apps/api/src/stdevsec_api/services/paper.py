"""Paper-trading service: accounts, positions, market-fill orders.

Simulation only. Long-only, no leverage: a sell can't exceed the held quantity.
Fills use the price supplied with the order (the live price the client observed).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from stdevsec_api.db.models import PaperAccount, PaperOrder, PaperPosition
from stdevsec_api.errors import DomainValidationError, NotFoundError
from stdevsec_api.schemas import PaperAccountCreate, PaperOrderCreate
from stdevsec_api.services.market import validate_symbol

_EPS = 1e-9  # tolerance for float quantity comparisons


def create_account(db: Session, payload: PaperAccountCreate) -> PaperAccount:
    account = PaperAccount(name=payload.name, cash=payload.initial_cash)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def list_accounts(db: Session, *, limit: int, offset: int) -> tuple[list[PaperAccount], int]:
    total = db.scalar(select(func.count()).select_from(PaperAccount)) or 0
    items = db.scalars(
        select(PaperAccount).order_by(PaperAccount.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), total


def get_account(db: Session, account_id: str) -> PaperAccount:
    account = db.get(PaperAccount, account_id)
    if account is None:
        raise NotFoundError(f"Paper account '{account_id}' not found")
    return account


def _position(account: PaperAccount, symbol: str) -> PaperPosition | None:
    return next((p for p in account.positions if p.symbol == symbol), None)


def place_order(db: Session, account_id: str, payload: PaperOrderCreate) -> PaperOrder:
    account = get_account(db, account_id)
    symbol = validate_symbol(payload.symbol)
    qty, price = payload.qty, payload.price
    pos = _position(account, symbol)

    if payload.side == "buy":
        cost = qty * price
        if cost > account.cash + _EPS:
            raise DomainValidationError(
                "Fondos insuficientes",
                details={"cost": cost, "cash": account.cash},
            )
        account.cash -= cost
        if pos is None:
            account.positions.append(PaperPosition(symbol=symbol, qty=qty, avg_price=price))
        else:
            new_qty = pos.qty + qty
            pos.avg_price = (pos.qty * pos.avg_price + qty * price) / new_qty
            pos.qty = new_qty
    else:  # sell
        if pos is None or qty > pos.qty + _EPS:
            raise DomainValidationError(
                "Posición insuficiente para vender",
                details={"held": pos.qty if pos else 0.0, "requested": qty},
            )
        account.cash += qty * price
        pos.qty -= qty
        if pos.qty <= _EPS:
            account.positions.remove(pos)  # flat -> drop the row

    order = PaperOrder(
        account_id=account.id, symbol=symbol, side=payload.side, qty=qty, price=price
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_orders(
    db: Session, account_id: str, *, limit: int, offset: int
) -> tuple[list[PaperOrder], int]:
    get_account(db, account_id)  # 404 if missing
    total = (
        db.scalar(
            select(func.count()).select_from(PaperOrder).where(PaperOrder.account_id == account_id)
        )
        or 0
    )
    items = db.scalars(
        select(PaperOrder)
        .where(PaperOrder.account_id == account_id)
        .order_by(PaperOrder.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total
