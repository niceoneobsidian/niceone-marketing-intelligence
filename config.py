"""Application configuration, loaded from the environment and validated at startup."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_LENGTH = 32

# Substrings that mark a value as a placeholder rather than a real secret.
_PLACEHOLDER_MARKERS = (
    "changeme",
    "change-me",
    "change_me",
    "replace-me",
    "replace_me",
    "placeholder",
    "example",
    "dummy",
    "your-secret",
    "your_secret",
)


class AppEnv(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"

    @property
    def is_shared(self) -> bool:
        """True for environments where weak secrets are not acceptable."""
        return self in {AppEnv.STAGING, AppEnv.PRODUCTION}


def _looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


class Settings(BaseSettings):
    """All runtime configuration. Environment variables use the ``NMI_`` prefix.

    The Phase 1 baseline is PostgreSQL plus local filesystem storage (ADR-0001). There is
    deliberately no Redis or object-storage setting: optional infrastructure is added only when
    justified, and must never become a required setting by accident.
    """

    model_config = SettingsConfigDict(
        env_prefix="NMI_",
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: AppEnv = AppEnv.LOCAL
    log_level: str = "INFO"

    secret_key: SecretStr
    database_url: SecretStr

    # Root directory for evidence and media files (local filesystem storage).
    storage_root: Path = Path(".local-data/evidence")

    cors_origins: list[str] = ["http://localhost:5173"]
    probe_timeout_seconds: float = 2.0

    @field_validator("log_level")
    @classmethod
    def _normalise_log_level(cls, value: str) -> str:
        level = value.upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            msg = f"invalid log level: {value!r}"
            raise ValueError(msg)
        return level

    @field_validator("probe_timeout_seconds")
    @classmethod
    def _positive_timeout(cls, value: float) -> float:
        if value <= 0:
            msg = "probe_timeout_seconds must be greater than zero"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_safe_for_shared_environments(self) -> Self:
        if not self.env.is_shared:
            return self

        problems: list[str] = []

        secret_key = self.secret_key.get_secret_value()
        if len(secret_key) < MIN_SECRET_LENGTH:
            problems.append(f"NMI_SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters")
        if _looks_like_placeholder(secret_key):
            problems.append("NMI_SECRET_KEY looks like a placeholder")

        if _looks_like_placeholder(self.database_url.get_secret_value()):
            problems.append("NMI_DATABASE_URL looks like it contains a placeholder")

        if not self.storage_root.is_absolute():
            problems.append("NMI_STORAGE_ROOT must be an absolute path")

        if problems:
            # Names the offending settings only; never echoes secret values.
            msg = f"unsafe configuration for {self.env.value}: " + "; ".join(problems)
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Load settings once per process. Raises if configuration is missing or unsafe."""
    return Settings()  # type: ignore[call-arg]  # required fields come from the environment
