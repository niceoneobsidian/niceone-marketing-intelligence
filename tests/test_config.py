from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import AppEnv, Settings
from tests.conftest import STRONG_SECRET, make_settings

SAFE_SHARED = {"secret_key": STRONG_SECRET, "storage_root": "/var/lib/nmi/evidence"}


def test_local_environment_accepts_simple_secrets() -> None:
    settings = make_settings()
    assert settings.env is AppEnv.LOCAL


def test_secrets_are_not_exposed_in_repr() -> None:
    settings = make_settings(secret_key="super-visible-canary")
    assert "super-visible-canary" not in repr(settings)
    assert "super-visible-canary" not in str(settings.model_dump())


def test_log_level_is_normalised() -> None:
    assert make_settings(log_level="debug").log_level == "DEBUG"


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_settings(log_level="loud")


def test_non_positive_probe_timeout_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make_settings(probe_timeout_seconds=0)


def test_storage_root_defaults_to_local_directory() -> None:
    assert make_settings().storage_root == Path(".local-data/evidence")


def test_redis_and_object_storage_are_not_configuration_requirements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Optional infrastructure must never become a required setting (ADR-0001)."""
    monkeypatch.setenv("NMI_SECRET_KEY", "local-dev-secret")
    monkeypatch.setenv("NMI_DATABASE_URL", "postgresql+psycopg://nmi:pw@localhost:5432/nmi")
    for name in ("NMI_REDIS_URL", "NMI_STORAGE_ENDPOINT_URL", "NMI_STORAGE_ACCESS_KEY"):
        monkeypatch.delenv(name, raising=False)
    assert Settings(_env_file=None).env is AppEnv.LOCAL  # type: ignore[call-arg]


@pytest.mark.parametrize("env", ["staging", "production"])
def test_shared_environments_accept_safe_configuration(env: str) -> None:
    settings = make_settings(env=env, **SAFE_SHARED)
    assert settings.env.is_shared


@pytest.mark.parametrize("env", ["staging", "production"])
def test_shared_environments_reject_short_secret_key(env: str) -> None:
    with pytest.raises(ValidationError, match="at least 32 characters"):
        make_settings(env=env, **{**SAFE_SHARED, "secret_key": "too-short"})


def test_production_rejects_placeholder_secret_key() -> None:
    with pytest.raises(ValidationError, match="placeholder"):
        make_settings(env="production", **{**SAFE_SHARED, "secret_key": "changeme-" + "x" * 32})


def test_production_rejects_placeholder_database_url() -> None:
    with pytest.raises(ValidationError, match="NMI_DATABASE_URL"):
        make_settings(
            env="production",
            database_url="postgresql+psycopg://nmi:changeme@db:5432/nmi",
            **SAFE_SHARED,
        )


def test_production_rejects_relative_storage_root() -> None:
    with pytest.raises(ValidationError, match="NMI_STORAGE_ROOT must be an absolute path"):
        make_settings(env="production", **{**SAFE_SHARED, "storage_root": "relative/evidence"})


def test_unsafe_configuration_error_never_echoes_secret_values() -> None:
    with pytest.raises(ValidationError) as excinfo:
        make_settings(env="production", **{**SAFE_SHARED, "secret_key": "leaky-short-canary"})
    assert "leaky-short-canary" not in str(excinfo.value)


def test_missing_required_setting_fails_fast(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("NMI_SECRET_KEY", "NMI_DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]
