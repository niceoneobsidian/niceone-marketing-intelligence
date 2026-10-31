"""Fixtures for tests that need a real PostgreSQL.

Select them explicitly with ``pytest -m integration``. They fail (rather than skip) when the
database is not configured, so a misconfigured CI job cannot pass by testing nothing.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.fixture(scope="session")
def real_settings() -> Settings:
    try:
        return Settings(_env_file=None)  # type: ignore[call-arg]
    except ValidationError as exc:
        pytest.fail(
            "Integration tests need NMI_* environment variables pointing at running services "
            f"(see .env.example and docs/setup.md): {exc.error_count()} setting(s) invalid"
        )
