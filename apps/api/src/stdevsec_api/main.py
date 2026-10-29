"""FastAPI application entrypoint.

Sprint 01 scope: liveness/readiness only, plus the cross-cutting concerns the
rest of the API will build on — CORS, a per-request correlation id, and
structured logging.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from stdevsec_api import __version__
from stdevsec_api.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
logger = logging.getLogger("stdevsec_api")

REQUEST_ID_HEADER = "X-Request-ID"


class HealthResponse(BaseModel):
    status: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    version: str
    checks: dict[str, str]


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="STDevsec Trading Lab API",
        version=__version__,
        description="Simulation-only quantitative research API. Not financial advice.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_and_logging(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "%s %s -> %s (%.1fms) request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
        )
        return response

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    async def health() -> HealthResponse:
        """Liveness: the process is up."""
        return HealthResponse(status="ok", version=__version__)

    @app.get("/ready", response_model=ReadyResponse, tags=["system"])
    async def ready() -> ReadyResponse:
        """Readiness: dependencies are reachable. Sprint 01 has no hard deps yet."""
        checks = {"quant_engine": "ok"}
        return ReadyResponse(status="ready", version=__version__, checks=checks)

    return app


app = create_app()
