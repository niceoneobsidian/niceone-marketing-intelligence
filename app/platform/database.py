"""PostgreSQL access via SQLAlchemy."""

from __future__ import annotations

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase

# Deterministic constraint names keep Alembic migrations stable and reviewable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_db_engine(database_url: str, *, connect_timeout_seconds: float = 2.0) -> Engine:
    """Build an engine. Connections are opened lazily, on first use."""
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args={"connect_timeout": max(1, round(connect_timeout_seconds))},
    )


def check_database(engine: Engine) -> None:
    """Raise if the database cannot execute a trivial query."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
