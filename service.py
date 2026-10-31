"""Readiness logic: run dependency probes and summarise the result.

Only dependencies registered as ``required`` can make the application not ready. Optional
dependencies that are unhealthy produce a ``degraded`` status. A dependency that is not
configured should not be registered at all, so optional infrastructure can never become
mandatory by accident (ADR-0001).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from app.modules.health.schemas import CheckStatus, DependencyCheck, ReadyResponse

logger = logging.getLogger("nmi.health")


@dataclass(frozen=True)
class DependencyProbe:
    """A named check that raises if its dependency is unhealthy."""

    name: str
    check: Callable[[], None]
    required: bool = True


def _run_probe(probe: DependencyProbe) -> DependencyCheck:
    started = time.perf_counter()
    try:
        probe.check()
    except Exception as exc:
        logger.warning(
            "readiness probe failed",
            extra={
                "dependency": probe.name,
                "required": probe.required,
                "error_type": type(exc).__name__,
            },
            exc_info=True,
        )
        status, error = CheckStatus.ERROR, type(exc).__name__
    else:
        status, error = CheckStatus.OK, None
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    return DependencyCheck(
        name=probe.name,
        required=probe.required,
        status=status,
        latency_ms=latency_ms,
        error=error,
    )


def run_readiness(probes: Sequence[DependencyProbe], *, environment: str) -> ReadyResponse:
    """Run all probes concurrently so one slow dependency cannot stall the others."""
    if probes:
        with ThreadPoolExecutor(max_workers=len(probes)) as pool:
            checks = list(pool.map(_run_probe, probes))
    else:
        checks = []

    failed = [check for check in checks if check.status is CheckStatus.ERROR]
    if any(check.required for check in failed):
        status = "not_ready"
    elif failed:
        status = "degraded"
    else:
        status = "ready"

    return ReadyResponse(
        status=status,
        environment=environment,
        checks=checks,
        degraded_capabilities=[check.name for check in failed if not check.required],
    )
