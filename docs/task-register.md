# Task Register

Status values: `done` (verified), `written-unverified` (code exists but has never been run), `blocked`, `not-started`.
Jira keys refer to the NMI project (obsidianintelligencehq.atlassian.net). Architecture baseline: [ADR-0001](adr/0001-lean-postgresql-baseline.md).

## Phase 0 — Repository inspection and governance

| ID | Task | Jira | Status | Notes |
|---|---|---|---|---|
| P0-01 | Inspect repository and working tree | — | done | No Git repo, project files or CI existed; GitHub token invalid. See `reports/phase-0-1-status.md`. |
| P0-02 | Do not overwrite or delete existing work | — | done | Nothing existed. Work is in a new `nmi/` directory. |
| P0-03 | Charter and engineering principles | NMI-11, NMI-13 | done | `charter.md`, `engineering-principles.md` |
| P0-04 | `AGENTS.md` | NMI-13 | done | |
| P0-05 | Architecture, roadmap and ADR | NMI-12 | done | ADR-0001 recorded. Roadmap authority is unresolved (D-01). |
| P0-06 | Task register and risk register | — | done | This file; `risk-register.md` |
| P0-07 | Identify product-owner decisions | — | done | `decisions-pending.md` (D-01 to D-12) |

## Phase 1 — Engineering foundation

| ID | Task | Jira | Status | Notes |
|---|---|---|---|---|
| P1-01 | FastAPI application infrastructure | NMI-13 | written-unverified | App factory, middleware, request IDs, error handling. Never imported or run. |
| P1-02 | PostgreSQL and Alembic migrations | NMI-15 | written-unverified | Baseline `system_metadata` migration only; never run. Domain schema (sources, content, snapshots, evidence, audit events — workspace-scoped) not started. |
| P1-03 | Identity and workspace isolation (users, workspaces, memberships, sessions, roles, permissions, audit events; Argon2id; CSRF; cross-workspace isolation tests) | NMI-37 | not-started | Unblocked by D-08 ([ADR-0002](adr/0002-authentication-and-workspace-authorization.md)); needs a password-hashing dependency, so it also needs registry access (D-09). Release gate: cross-workspace access tests must pass. |
| P1-04 | PostgreSQL-backed background jobs | — | not-started | Initial queue per ADR-0001. |
| P1-05 | Local filesystem storage behind a storage interface | NMI-16 | written-unverified | `platform/storage.py` plus unit tests; never run. Evidence validation/hashing/quarantine services not started. |
| P1-06 | Health and readiness endpoints | NMI-13 | written-unverified | Required/optional readiness per ADR-0001; unit and integration tests written, never run. |
| P1-07 | Secure configuration and secret validation | NMI-38 | written-unverified | `core/config.py` plus tests. Dependency pinning/scanning not started. |
| P1-08 | Structured logging | NMI-13, NMI-38 | written-unverified | `core/logging.py` plus tests; never run. |
| P1-09 | React + TypeScript frontend skeleton | NMI-34 | not-started | Blocked by registry access (R-09). |
| P1-10 | Docker Compose (PostgreSQL only) | NMI-39 | written-unverified | Passes `docker compose config`; never run (no daemon). Redis and MinIO intentionally absent. |
| P1-11 | Dependency management and locks | NMI-13, NMI-38 | blocked | `pyproject.toml` written; `uv.lock` cannot be generated (R-09). |
| P1-12 | Quality checks (ruff, mypy, pytest; frontend lint/type/test/build) | NMI-13 | blocked | Configured; none executed. |
| P1-13 | Automated CI (tests, ruff, mypy, security checks) | NMI-38, NMI-39 | not-started | Should include dependency and secret scanning. |
| P1-14 | Setup and troubleshooting docs | NMI-13 | not-started | Write after the stack has actually been run. |
| P1-15 | Phase completion report | — | blocked | Interim status in `reports/phase-0-1-status.md`. |

## Exit gate status

Phase 0: passed. Phase 1: **not passed**. Do not start the next phase.
