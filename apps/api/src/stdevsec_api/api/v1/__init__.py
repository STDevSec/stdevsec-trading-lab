"""API v1 routers."""

from fastapi import APIRouter

from stdevsec_api.api.v1 import backtests, datasets, journal, paper, strategies

router = APIRouter(prefix="/api/v1")
router.include_router(datasets.router)
router.include_router(strategies.router)
router.include_router(backtests.router)
router.include_router(journal.router)
router.include_router(paper.router)
