"""Shared test helpers."""

from __future__ import annotations

from typing import Any

from app.core.config import Settings

STRONG_SECRET = "k3V9xQ2mZp7LwR4tYb8NcD1fHs6JgAe0"  # 32 chars, no placeholder markers


def make_settings(**overrides: Any) -> Settings:
    """Build Settings from explicit values only, ignoring any .env file or environment."""
    values: dict[str, Any] = {
        "env": "local",
        "secret_key": "local-dev-secret",
        "database_url": "postgresql+psycopg://nmi:pw@localhost:5432/nmi",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)
