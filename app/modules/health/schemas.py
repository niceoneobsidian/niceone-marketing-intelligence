"""Response models for the health module."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class CheckStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


class DependencyCheck(BaseModel):
    name: str
    # Required dependencies make the app not ready when unhealthy; optional ones only degrade it.
    required: bool
    status: CheckStatus
    latency_ms: float
    # Exception class name only. Messages can contain hostnames or credentials, so the
    # full detail goes to the logs, never the response.
    error: str | None = None


class LiveResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(BaseModel):
    # ready:     every dependency is healthy.
    # degraded:  required dependencies are healthy; one or more optional ones are not.
    # not_ready: a required dependency is unhealthy.
    status: Literal["ready", "degraded", "not_ready"]
    environment: str
    checks: list[DependencyCheck]
    degraded_capabilities: list[str] = Field(default_factory=list)
