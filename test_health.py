from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from app.main import REQUEST_ID_HEADER, create_app
from app.modules.health.service import DependencyProbe, run_readiness
from tests.conftest import make_settings


def _ok() -> None:
    return None


def _fail_with_secret() -> None:
    msg = "could not connect to postgresql://nmi:hunter2@db.internal:5432/nmi"
    raise ConnectionError(msg)


def _client(*probes: DependencyProbe) -> TestClient:
    return TestClient(create_app(make_settings(), probes=list(probes)))


def _by_name(body: dict[str, object]) -> dict[str, dict[str, object]]:
    checks = body["checks"]
    assert isinstance(checks, list)
    return {c["name"]: c for c in checks}


# --- liveness -----------------------------------------------------------------------------


def test_live_returns_ok_without_checking_dependencies() -> None:
    client = _client(DependencyProbe("postgres", _fail_with_secret))
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- readiness rules (ADR-0001) -------------------------------------------------------------


def test_ready_when_all_dependencies_are_healthy() -> None:
    client = _client(
        DependencyProbe("postgres", _ok, required=True),
        DependencyProbe("local_storage", _ok, required=False),
    )
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["environment"] == "local"
    assert body["degraded_capabilities"] == []
    assert all(c["error"] is None for c in body["checks"])


def test_not_ready_when_postgres_is_unavailable() -> None:
    client = _client(
        DependencyProbe("postgres", _fail_with_secret, required=True),
        DependencyProbe("local_storage", _ok, required=False),
    )
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert _by_name(body)["postgres"]["status"] == "error"
    assert _by_name(body)["postgres"]["required"] is True
    assert body["degraded_capabilities"] == []


def test_degraded_but_still_ready_when_an_optional_dependency_fails() -> None:
    client = _client(
        DependencyProbe("postgres", _ok, required=True),
        DependencyProbe("local_storage", _fail_with_secret, required=False),
    )
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200  # an optional failure must not fail readiness
    body = response.json()
    assert body["status"] == "degraded"
    assert body["degraded_capabilities"] == ["local_storage"]
    assert _by_name(body)["postgres"]["status"] == "ok"
    assert _by_name(body)["local_storage"]["status"] == "error"


def test_required_failure_outranks_optional_failure() -> None:
    result = run_readiness(
        [
            DependencyProbe("postgres", _fail_with_secret, required=True),
            DependencyProbe("local_storage", _fail_with_secret, required=False),
        ],
        environment="local",
    )
    assert result.status == "not_ready"
    assert result.degraded_capabilities == ["local_storage"]


def test_unconfigured_optional_infrastructure_is_simply_not_probed() -> None:
    """With only PostgreSQL registered (no Redis, no object store) the app is ready."""
    client = _client(DependencyProbe("postgres", _ok, required=True))
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert [c["name"] for c in body["checks"]] == ["postgres"]


def test_probes_default_to_required() -> None:
    assert DependencyProbe("postgres", _ok).required is True


def test_ready_with_no_probes_is_ready() -> None:
    result = run_readiness([], environment="local")
    assert result.status == "ready"
    assert result.checks == []


# --- safety of the readiness response ---------------------------------------------------------


def test_ready_response_does_not_leak_error_details() -> None:
    client = _client(DependencyProbe("postgres", _fail_with_secret))
    response = client.get("/api/v1/health/ready")

    assert response.json()["checks"][0]["error"] == "ConnectionError"
    assert "hunter2" not in response.text
    assert "db.internal" not in response.text


def test_failed_probe_is_logged_with_dependency_name(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="nmi.health"):
        run_readiness([DependencyProbe("local_storage", _fail_with_secret, False)], "local")
    record = next(r for r in caplog.records if r.name == "nmi.health")
    assert record.__dict__["dependency"] == "local_storage"
    assert record.__dict__["required"] is False


def test_probe_latency_is_recorded() -> None:
    result = run_readiness([DependencyProbe("postgres", _ok)], environment="local")
    assert result.checks[0].latency_ms >= 0


# --- request context and error handling ---------------------------------------------------------


def test_response_includes_generated_request_id() -> None:
    response = _client().get("/api/v1/health/live")
    assert len(response.headers[REQUEST_ID_HEADER]) == 32


def test_well_formed_client_request_id_is_echoed() -> None:
    response = _client().get("/api/v1/health/live", headers={REQUEST_ID_HEADER: "trace-abc.123"})
    assert response.headers[REQUEST_ID_HEADER] == "trace-abc.123"


def test_malformed_client_request_id_is_replaced() -> None:
    bad = "x" * 200
    response = _client().get("/api/v1/health/live", headers={REQUEST_ID_HEADER: bad})
    assert response.headers[REQUEST_ID_HEADER] != bad
    assert len(response.headers[REQUEST_ID_HEADER]) == 32


def test_unhandled_exception_returns_generic_500_with_request_id() -> None:
    app = create_app(make_settings(), probes=[])

    @app.get("/boom")
    def boom() -> None:
        msg = "internal detail that must not leak"
        raise RuntimeError(msg)

    response = TestClient(app).get("/boom")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "internal detail" not in response.text
    assert REQUEST_ID_HEADER in response.headers


def test_cors_allows_configured_origin_only() -> None:
    client = _client()
    allowed = client.get("/api/v1/health/live", headers={"Origin": "http://localhost:5173"})
    denied = client.get("/api/v1/health/live", headers={"Origin": "http://evil.example"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers
