# Implementation Roadmap

> **Roadmap authority is unresolved (D-01).** The directive refers to an approved 16-phase roadmap. The project plan held in the Project docs defines 12 phases (P0–P11) and describes itself as a "proposed baseline — pending configuration approval". Its P1 (repository foundation) and P2 (runtime and persistence) also split work that the directive groups as "Phase 1". This document follows the directive's Phase 0 / Phase 1 scope and lists the plan's phases for reference only.

## Phase 0 — Repository inspection and governance

Scope: inspect repository and working tree; establish charter, engineering principles, `AGENTS.md`, architecture and roadmap docs, ADR, task register, risk register, and the list of product-owner decisions.

Exit gate:

- [x] Repository state inspected and recorded (see `reports/phase-0-1-status.md`).
- [x] No existing work overwritten or deleted.
- [x] Charter, principles, `AGENTS.md`, architecture, roadmap and ADR-0001 present.
- [x] Task register and risk register present.
- [x] Product-owner decisions identified (`decisions-pending.md`).

## Phase 1 — Engineering foundation

Baseline: [ADR-0001](adr/0001-lean-postgresql-baseline.md) — PostgreSQL-centred; Redis and MinIO deferred.

Scope: FastAPI application infrastructure; PostgreSQL and Alembic migrations; identity and workspace isolation; PostgreSQL-backed background jobs; local filesystem storage behind a storage interface; React + TypeScript frontend; Docker Compose (PostgreSQL); locked dependencies; validated configuration; structured logging; health and readiness endpoints; backend and frontend quality checks; CI with security checks; setup and troubleshooting docs.

Exit gate (each item must be demonstrated with actual command output):

1. Application starts locally.
2. Frontend can communicate with the backend.
3. Database connectivity works.
4. Readiness behaves per ADR-0001: PostgreSQL down → not ready; optional infrastructure unconfigured → ready; optional dependency unavailable → degraded.
5. Migrations upgrade from an empty database and downgrade safely.
6. Backend tests pass.
7. Frontend tests and build pass.
8. Linting and type checks pass.
9. CI is configured and its result is verified where execution is available.

**Current status: NOT passed.** Blocked by registry access (R-09, D-09); no gate has been demonstrated. See `task-register.md`.

## Project plan phases (reference only; unapproved)

| Plan phase | Focus | Exit condition |
|---|---|---|
| P0 | Product definition and governance | Scope and boundaries approved |
| P1 | Repository foundation | Fresh clone passes checks |
| P2 | Core runtime and persistence (API, settings, PostgreSQL, migrations, jobs) | App starts; persistence and jobs work |
| P3 | Evidence and collection contracts | Contract tests pass |
| P4 | First collection providers | Permitted source captured reproducibly |
| P5 | Media ingestion | Media processing is traceable |
| P6 | Profile and content intelligence | Claims link to evidence |
| P7 | Psychology, virality, frameworks | Repeated evidence supports implicit frameworks |
| P8 | Framework library and reports | Frameworks retrievable and traceable |
| P9 | Dashboard vertical slice | End-to-end user workflow works |
| P10 | Security and release hardening | Release gates pass |
| P11 | Platform expansion | Each adapter passes conformance tests |

Do not begin anything beyond Phase 1 until Phase 1 has passed its exit gate and the product owner assigns the next phase.
