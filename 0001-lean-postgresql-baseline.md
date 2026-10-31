# ADR-0001: Lean, PostgreSQL-centred Phase 1 baseline (defer Redis and MinIO)

- **Status:** Accepted — decided by the product owner on 2026-10-31; the two inferred points were confirmed the same day (see "Confirmations").
- **Jira:** NMI-12 (record final architecture decisions), NMI-15 (PostgreSQL schema), NMI-16 (storage abstraction), NMI-39 (deployment and release)
- **Supersedes:** the Redis, MinIO and Redis-backed worker choices in `niceone_marketing_intelligence_spec.md` §3.1, §5.1 and §5.2, and the Redis/MinIO items in the original Phase 1 directive.

## Context

NMI is a standalone, local-first, lean-cost product (NMI-1). The project plan states "no mandatory paid API", durable PostgreSQL job states, and an explicit rule to "add a provider only when … a documented capability gap justifies its maintenance cost". Nothing yet demonstrates a need for a separate queue broker or object-storage service.

## Decision

| Component | Phase 1 | Rationale |
|---|---|---|
| PostgreSQL | **Adopt** | Primary application database. |
| PostgreSQL-backed jobs | **Adopt** | Initial queue. Redis is introduced only when justified. |
| Redis | **Defer — do not install** | PostgreSQL-backed jobs are the initial queue. |
| MinIO | **Defer — do not install** | No demonstrated need for a separate object-storage service. |
| Local filesystem storage | **Adopt** | Initial evidence and media storage. |
| Storage abstraction | **Adopt** | Allows later migration to MinIO or another object store. |
| pgvector | Planned direction; not built in Phase 1 *(inferred)* | Supports planned semantic retrieval. |
| Ollama | Planned direction; not built in Phase 1 *(inferred)* | Avoids mandatory hosted-model API costs. |

## Readiness semantics

Readiness must reflect actual required dependencies and must not turn optional infrastructure into mandatory infrastructure.

| Situation | Result |
|---|---|
| PostgreSQL unavailable | **not ready** (HTTP 503) |
| Redis not configured | **ready** (it is not probed) |
| MinIO not configured | **ready** (it is not probed) |
| An optional integration is unavailable | **degraded** (HTTP 200): the unavailable capability is listed in `degraded_capabilities`; the app is not failed |

Implementation rules: a dependency that is not configured is not registered as a probe. Each probe is explicitly `required` or optional. Only a failed *required* probe yields `not_ready`.

In Phase 1, local evidence storage is registered as an **optional** probe. When storage is unavailable the application reports degraded capability and the evidence-write path must **fail explicitly**: it must never silently accept evidence that cannot be persisted.

## Phase 1 implementation scope

FastAPI application infrastructure; PostgreSQL and Alembic migrations; identity and workspace isolation; PostgreSQL-backed background jobs; local filesystem storage behind a storage interface; health and readiness endpoints; secure configuration and CI checks.

## Jira mapping

| Decision or implementation | Jira |
|---|---|
| Record final architecture decisions | NMI-12 |
| Implement PostgreSQL schema | NMI-15 |
| Implement storage abstraction | NMI-16 |
| Configure deployment and release | NMI-39 |

## Proposed triggers for revisiting (pending approval)

NMI-12 asks the ADRs to state triggers for adding Redis or separate workers. These are **proposals**, not approved rules:

- **Redis:** measured queue latency or database load attributable to PostgreSQL job polling that cannot be resolved by tuning; or a measured caching or cross-worker rate-limiting need.
- **Separate workers:** job execution that must scale or fail independently of the API process, shown by measurement.
- **MinIO / object store:** a multi-node deployment needing shared storage, evidence volume outgrowing a single host's disk plan, or a requirement for lifecycle or presigned-URL features.

Any such change requires a new ADR.

## Consequences

- Fewer moving parts and a simpler local setup (PostgreSQL only).
- Job throughput is bounded by PostgreSQL until a trigger is met.
- Local filesystem storage ties evidence to one host until the abstraction gains a second implementation.
- The original spec is now inconsistent with this decision (and with the plan on collection vendors); see `decisions-pending.md` D-11.

## Confirmations (2026-10-31)

1. pgvector and Ollama are planned but not built in Phase 1; Redis and MinIO remain deferred.
2. Local evidence storage is an optional (degraded) readiness dependency, not a required one. PostgreSQL is the only mandatory external infrastructure dependency.
