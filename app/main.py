"""Application factory.

Run with: ``uvicorn app.main:create_app --factory``
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, request_id_ctx
from app.modules.health.api import router as health_router
from app.modules.health.service import DependencyProbe
from app.platform.database import check_database, create_db_engine
from app.platform.storage import LocalFilesystemStorage

API_PREFIX = "/api/v1"
REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

access_logger = logging.getLogger("nmi.access")
error_logger = logging.getLogger("nmi.error")


def build_default_probes(settings: Settings) -> tuple[list[DependencyProbe], Callable[[], None]]:
    """Create the real dependency probes and a function that releases their resources.

    PostgreSQL is the only required dependency. Local evidence storage is optional: if it is
    unavailable the app stays ready and reports degraded capability (ADR-0001). Infrastructure
    that is not part of the baseline (Redis, object storage) is not probed at all.
    """
    engine = create_db_engine(
        settings.database_url.get_secret_value(),
        connect_timeout_seconds=settings.probe_timeout_seconds,
    )

    storage = LocalFilesystemStorage(settings.storage_root)
    try:
        storage.ensure_root()
    except OSError:
        # Not fatal: the storage probe will report the problem as degraded capability.
        logging.getLogger("nmi").warning("could not create storage root", exc_info=True)

    probes = [
        DependencyProbe("postgres", partial(check_database, engine), required=True),
        DependencyProbe("local_storage", storage.check_health, required=False),
    ]
    return probes, engine.dispose


def _request_id_from(request: Request) -> str:
    supplied = request.headers.get(REQUEST_ID_HEADER, "")
    # Only accept well-formed IDs so callers cannot inject arbitrary text into logs.
    return supplied if _VALID_REQUEST_ID.fullmatch(supplied) else uuid.uuid4().hex


def create_app(
    settings: Settings | None = None,
    probes: Sequence[DependencyProbe] | None = None,
) -> FastAPI:
    """Build the application. ``probes`` can be injected for tests."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    close_resources: Callable[[], None] = lambda: None  # noqa: E731
    if probes is None:
        probes, close_resources = build_default_probes(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logging.getLogger("nmi").info("starting", extra={"environment": settings.env.value})
        yield
        close_resources()
        logging.getLogger("nmi").info("stopped")

    app = FastAPI(title="NMI API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.probes = probes

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=[REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = _request_id_from(request)
        token = request_id_ctx.set(request_id)
        started = time.perf_counter()
        try:
            try:
                response = await call_next(request)
            except Exception:
                error_logger.exception("unhandled exception")
                response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
            response.headers[REQUEST_ID_HEADER] = request_id
            access_logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                },
            )
            return response
        finally:
            request_id_ctx.reset(token)

    app.include_router(health_router, prefix=API_PREFIX)
    return app
