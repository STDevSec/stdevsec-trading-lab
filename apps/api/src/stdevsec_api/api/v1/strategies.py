"""Strategy catalog endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from stdevsec_api.schemas import StrategyInfo
from stdevsec_api.services.strategies import CATALOG

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("", response_model=list[StrategyInfo])
def list_strategies() -> list[StrategyInfo]:
    return CATALOG
