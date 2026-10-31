"""HTTP surface of the health module."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.config import Settings
from app.modules.health.schemas import LiveResponse, ReadyResponse
from app.modules.health.service import DependencyProbe, run_readiness

router = APIRouter(prefix="/health", tags=["health"])


def get_probes(request: Request) -> Sequence[DependencyProbe]:
    probes: Sequence[DependencyProbe] = request.app.state.probes
    return probes


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


@router.get("/live", response_model=LiveResponse, summary="Liveness")
def live() -> LiveResponse:
    """The process is running. Deliberately checks no dependencies."""
    return LiveResponse()


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"model": ReadyResponse, "description": "A required dependency is unhealthy"}},
    summary="Readiness",
)
def ready(
    response: Response,
    probes: Annotated[Sequence[DependencyProbe], Depends(get_probes)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ReadyResponse:
    """Returns 503 only when a required dependency (PostgreSQL) is unhealthy.

    Unhealthy optional dependencies return 200 with status ``degraded`` and are listed in
    ``degraded_capabilities``.
    """
    result = run_readiness(probes, environment=settings.env.value)
    if result.status == "not_ready":
        response.status_code = 503
    return result
