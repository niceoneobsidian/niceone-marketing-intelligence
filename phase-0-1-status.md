# Phase 0–1 Status Report (interim — Phase 1 NOT complete)

Date: 2026-10-30

## Summary

Phase 0 is complete. Phase 1 is **blocked**: the build environment's egress policy denies the Python and npm package registries, so dependencies cannot be installed. No lock file, test run, lint run, type check, frontend build or app start has been performed. Nothing in this report claims otherwise.

## Repository inspection (Phase 0)

| Item | Finding |
|---|---|
| Working directory | `/home/claude`, not a Git repository |
| Existing branch / commit | none |
| Uncommitted changes | none (no repository) |
| Existing project files | none |
| Existing CI | none (`.github/workflows` absent) |
| GitHub access | `gh` reports the session token invalid; no NMI repository could be identified or reached |
| Toolchain present | Python 3.13, Node 22, Docker client 29.9 (daemon not running), `uv`, `psql`, PostgreSQL 16 binaries, `redis-server` |

No existing work was overwritten or deleted. A new repository was initialised in `/home/claude/nmi` on branch `phase-0-1/engineering-foundation`. **No commits have been made; there is no commit SHA.** Nothing has been pushed.

## What exists

- Governance: `AGENTS.md`, `docs/charter.md`, `engineering-principles.md`, `architecture.md`, `roadmap.md`, `task-register.md`, `risk-register.md`, `decisions-pending.md`, `.gitignore`.
- Backend source (written, **unverified**): configuration with secret validation, JSON logging with request IDs, PostgreSQL/Redis/object-storage adapters, health module (`/api/v1/health/live`, `/ready`), application factory, Alembic config and baseline migration, `pyproject.toml`.
- Backend tests (written, **never executed**): unit tests for config, logging and health; integration tests for real service connectivity, degraded readiness and migration up/down.

## Checks actually run

| Check | Result |
|---|---|
| `uv lock` | Failed: DNS could not resolve pypi.org |
| Same via session proxy | Failed: proxy answered HTTP 403 (policy denial) for pypi.org and registry.npmjs.org |
| `uv lock --offline` | Failed: required packages (e.g. alembic) not in local cache |
| `python -m compileall app tests alembic` | Passed — syntax only; no imports resolved, no behaviour tested |

Not run: pytest, ruff, mypy, frontend tests/lint/typecheck/build, `alembic upgrade`, application start, Docker Compose, CI.

## Update — 2026-10-31: architecture decision applied (ADR-0001)

The product owner decided on a lean, PostgreSQL-centred baseline: Redis and MinIO are deferred (not installed), jobs are PostgreSQL-backed, evidence is stored on the local filesystem behind a storage interface, and readiness must not make optional infrastructure mandatory. Recorded in `docs/adr/0001-lean-postgresql-baseline.md`, mapped to NMI-12, NMI-15, NMI-16 and NMI-39.

Changes made (all **written-unverified**):

- Removed the Redis adapter, Redis/object-storage settings, the `redis` dependency, and the endpoint-reachability storage check.
- Added `platform/storage.py`: `EvidenceStorage` protocol and `LocalFilesystemStorage` (key validation, no path traversal or symlink escape, immutable and idempotent writes, atomic writes, SHA-256 returned).
- Readiness now distinguishes required and optional probes: `ready` / `degraded` (HTTP 200) / `not_ready` (HTTP 503). Only PostgreSQL is required; local storage is optional.
- `docker-compose.yml` provides PostgreSQL only; `.env.example` added.
- Unit tests added/updated for config, health (including the four readiness rules) and storage; integration tests updated.

Checks run after these changes:

| Check | Result |
|---|---|
| `python -m compileall app tests alembic` | Passed (syntax only) |
| `docker compose --env-file .env.example config` | Passed |
| `docker compose config` with no environment | Fails with clear "required variable ... is missing" errors, as intended |
| Leftover Redis/MinIO references in `app/`, `tests/`, `alembic/`, `pyproject.toml` | Only explanatory comments and one guard test remain |

Still not run: pytest, ruff, mypy, migrations, application start, frontend, CI. The registry blocker (D-09) is unchanged.

Not yet started although in Phase 1 scope: identity and workspace isolation (needs D-08), PostgreSQL-backed jobs, frontend, CI, setup docs.

New findings from the Project docs and Jira are recorded as D-01, D-10, D-11, D-12 and risks R-10, R-11.

## Update — 2026-10-31: authentication decision recorded (ADR-0002)

Recorded from the product owner's memo: D-08 resolved (first-party email/password, Argon2id, opaque PostgreSQL-backed sessions, cookies with CSRF protection, workspace-scoped RBAC, no public self-registration); D-10 approved (keep current layout); D-11 superseded (`spec-supersessions.md`); D-12 approved; D-01 kept provisional.

Documentation only. **No identity, session, or authorization code has been written.**

Runtime status is unchanged and remains unverified:

| Item | State |
|---|---|
| Syntax compilation | Completed (syntax only; not evidence of runtime correctness) |
| Docker Compose configuration validation | Completed (`docker compose config`; stack never run) |
| Dependency installation | Blocked (registries denied, D-09) |
| Lock-file generation | Blocked |
| Unit and integration tests | Not run |
| Application startup | Not verified |
| Git commit and remote | Not created |

Release gate for authentication: cross-workspace access tests must prove one workspace cannot read or modify another's data.

## Exit gates

Phase 0: passed. Phase 1 gates 1–9: **none demonstrated.**

## Known limitations

- Package registries unreachable (R-09); Docker daemon unavailable (R-03); CI cannot run here (R-04); no reachable remote repository (R-02).
- Local-storage readiness only checks that the storage root is an existing, writable directory; it does not exercise a write.
- Source in this directory has never been imported or executed; expect it may contain defects that only a real run will reveal.

## Unresolved decisions

See `decisions-pending.md` (D-01 to D-12). D-09 (registry access) is blocking; D-08 (authentication approach) blocks identity and workspace isolation.

## Recommendation

Do not start Phase 2. To finish Phase 1, grant the session access to `pypi.org`, `files.pythonhosted.org` and `registry.npmjs.org` (or supply an approved internal mirror), and ideally a running Docker daemon and the canonical GitHub repository. Then re-run this assignment: the remaining work is generating locks, running and fixing the written backend, building the frontend, Compose, CI and setup docs, and producing the real completion report.
