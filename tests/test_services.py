from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app
from app.platform.database import check_database, create_db_engine

pytestmark = pytest.mark.integration


def _ready(settings: Settings) -> tuple[int, dict[str, object]]:
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/health/ready")
    return response.status_code, response.json()


def test_database_connectivity(real_settings: Settings) -> None:
    engine = create_db_engine(real_settings.database_url.get_secret_value())
    try:
        check_database(engine)
    finally:
        engine.dispose()


def test_readiness_is_ready_with_real_postgres_and_writable_storage(
    real_settings: Settings, tmp_path: Path
) -> None:
    settings = real_settings.model_copy(update={"storage_root": tmp_path / "evidence"})
    status_code, body = _ready(settings)

    assert status_code == 200, body
    assert body["status"] == "ready"
    assert {c["name"]: c["status"] for c in body["checks"]} == {  # type: ignore[attr-defined]
        "postgres": "ok",
        "local_storage": "ok",
    }


def test_readiness_is_not_ready_when_postgres_is_unreachable(
    real_settings: Settings, tmp_path: Path
) -> None:
    # Port 1 is reserved and never has a listener.
    unreachable = SecretStr("postgresql+psycopg://nmi:wrong@127.0.0.1:1/nmi")
    settings = real_settings.model_copy(
        update={"database_url": unreachable, "storage_root": tmp_path / "evidence"}
    )
    status_code, body = _ready(settings)

    assert status_code == 503
    assert body["status"] == "not_ready"
    statuses = {c["name"]: c["status"] for c in body["checks"]}  # type: ignore[attr-defined]
    assert statuses == {"postgres": "error", "local_storage": "ok"}


def test_readiness_is_degraded_but_200_when_storage_is_unusable(
    real_settings: Settings, tmp_path: Path
) -> None:
    # A regular file where the storage directory should be: unusable even for root.
    broken_root = tmp_path / "not-a-directory"
    broken_root.write_text("x")
    settings = real_settings.model_copy(update={"storage_root": broken_root})
    status_code, body = _ready(settings)

    assert status_code == 200
    assert body["status"] == "degraded"
    assert body["degraded_capabilities"] == ["local_storage"]
    statuses = {c["name"]: c["status"] for c in body["checks"]}  # type: ignore[attr-defined]
    assert statuses == {"postgres": "ok", "local_storage": "error"}
