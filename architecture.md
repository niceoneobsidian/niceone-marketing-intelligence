# Architecture

Governing decision: [ADR-0001](adr/0001-lean-postgresql-baseline.md) — a lean, PostgreSQL-centred baseline.

## Style

Modular monolith. A single FastAPI application serves the API; a single React + TypeScript single-page application is the UI. There are no other deployable services in Phase 1.

## Components (Phase 1 baseline)

| Component | Technology | Role |
|---|---|---|
| Backend | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic | HTTP API, domain logic, migrations |
| Frontend | React, TypeScript, Vite, Vitest | UI |
| Database | PostgreSQL 16 | System of record; initial job queue |
| Evidence/media storage | Local filesystem behind a storage interface | Evidence and media files |

Not part of the Phase 1 baseline (do not install): **Redis**, **MinIO**. Planned, not built in Phase 1: pgvector (semantic retrieval), local Ollama (AI runtime).

## Backend layout

```
backend/app/
  main.py            application factory, middleware, router wiring
  core/              cross-cutting: config, logging, request context
  platform/          infrastructure adapters: database, storage
  modules/<domain>/  one folder per domain
    api.py           FastAPI router (the module's public HTTP surface)
    service.py       domain logic
    schemas.py       Pydantic models
```

Rules:

- A module may import from `core/` and `platform/`, never from another module's internals.
- Cross-module use goes through the other module's `service.py` public functions.
- `platform/` adapters know nothing about domains.

Implemented so far: the `health` module, the database adapter, and the storage interface with its local filesystem implementation. Identity and workspace isolation ([ADR-0002](adr/0002-authentication-and-workspace-authorization.md)) and PostgreSQL-backed jobs are in scope for Phase 1 but not yet started.

## Storage interface

`app/platform/storage.py` defines the `EvidenceStorage` protocol (`put`, `get`, `exists`, `check_health`). Phase 1 implements `LocalFilesystemStorage`:

- Keys are restricted to a safe character set and depth; path traversal and symlink escape are rejected.
- Objects are immutable: identical re-writes are idempotent; different bytes for an existing key raise an error.
- Writes are atomic (temporary file, fsync, no-overwrite hard link).
- `put` returns the size and SHA-256 so callers can verify evidence by reference.

A future object-store implementation must satisfy the same protocol.

## API conventions

- All endpoints live under `/api/v1`.
- Liveness: `GET /api/v1/health/live` — process is up; no dependency checks.
- Readiness: `GET /api/v1/health/ready` — see the table below.
- Every response carries an `X-Request-ID` header; the same ID appears in that request's log lines.

### Readiness semantics

| Situation | `status` | HTTP |
|---|---|---|
| All dependencies healthy | `ready` | 200 |
| A required dependency (PostgreSQL) unhealthy | `not_ready` | 503 |
| Only optional dependencies unhealthy (e.g. local storage) | `degraded`, with `degraded_capabilities` listed | 200 |
| Redis / MinIO / other infrastructure not configured | not probed; no effect | — |

Error details are never returned in the response (only the exception class name); full details go to the logs.

## Configuration

Environment variables (`NMI_` prefix), validated by `pydantic-settings` at startup (`core/config.py`). Required: `NMI_SECRET_KEY`, `NMI_DATABASE_URL`. In `staging` and `production`, short or placeholder secrets and a relative storage path abort startup. There are intentionally no Redis or object-storage settings. See `.env.example`.

## Frontend layout (planned)

```
frontend/src/
  api/        typed API client
  App.tsx     Phase 1 status page (calls the readiness endpoint)
```

In development the Vite dev server proxies `/api` to the backend. Not yet started.

## Integration boundary

NMI exposes no integration with other NICEONE applications. Any future integration must be a documented, versioned external interface approved by the product owner.
