"""Verify Alembic migrations apply and revert cleanly on a scratch database."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from app.core.config import Settings

pytestmark = pytest.mark.integration

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def scratch_database_url(real_settings: Settings) -> Iterator[str]:
    base = make_url(real_settings.database_url.get_secret_value())
    name = f"nmi_migration_test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    try:
        yield base.set(database=name).render_as_string(hide_password=False)
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


def _alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def test_upgrade_head_then_downgrade_base(scratch_database_url: str) -> None:
    config = _alembic_config(scratch_database_url)
    engine = create_engine(scratch_database_url)
    try:
        command.upgrade(config, "head")
        tables = set(inspect(engine).get_table_names())
        assert {"system_metadata", "alembic_version"} <= tables

        columns = {c["name"] for c in inspect(engine).get_columns("system_metadata")}
        assert columns == {"key", "value", "updated_at"}

        command.downgrade(config, "base")
        remaining = set(inspect(engine).get_table_names())
        assert "system_metadata" not in remaining
    finally:
        engine.dispose()


def test_models_match_migrations(scratch_database_url: str) -> None:
    """Autogenerate must find no drift between ORM models and the migration history."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext

    from app.platform import models  # noqa: F401
    from app.platform.database import Base

    config = _alembic_config(scratch_database_url)
    command.upgrade(config, "head")

    engine = create_engine(scratch_database_url)
    try:
        with engine.connect() as connection:
            diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert diff == []
    finally:
        engine.dispose()
