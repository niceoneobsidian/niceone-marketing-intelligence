# ADR-0002: Independent first-party authentication with PostgreSQL-backed sessions

- **Status:** Accepted — decided 2026-10-31 (resolves D-08), taken from the product owner's attached decision memo.
- **Jira:** NMI-37 (workspace access control, privacy and audit safeguards); NMI-38 (secure configuration and dependency controls)
- **Related:** [ADR-0001](0001-lean-postgresql-baseline.md) (PostgreSQL-centred baseline, no Redis)

## Context

NMI must operate independently. It must not depend on an OIS authentication service or any external identity provider (charter; project plan §3). ADR-0001 excludes Redis from Phase 1, so session state must live in PostgreSQL.

## Decision

| Component | Phase 1 decision |
|---|---|
| Identity | NMI-managed user accounts |
| Login | Email + password |
| Password hashing | Argon2id |
| Session model | Opaque, server-side sessions |
| Session storage | PostgreSQL |
| Browser transport | Secure, HttpOnly, SameSite cookies |
| CSRF protection | Required for state-changing browser requests |
| Authorization | Workspace-scoped RBAC |
| Audit | Login, logout, membership and permission changes |
| External identity providers | Deferred |
| JWT access/refresh tokens | Not required for the initial browser application |

### Why PostgreSQL-backed sessions rather than JWTs

- Immediate session revocation.
- No Redis dependency.
- No refresh-token rotation system to maintain.
- Centralised session and user state.
- Straightforward workspace authorization.
- Fewer moving parts for a modular monolith.

### Initial entities

`users`, `workspaces`, `workspace_memberships`, `sessions`, `roles`, `permissions`, `audit_events`.

### Initial roles

| Role | Permissions |
|---|---|
| Owner | Full workspace control |
| Admin | Manage members, settings and operations |
| Analyst | Access evidence, intelligence and reports |
| Viewer | Read-only access |

### Tenant isolation

Every workspace-owned record must enforce tenant isolation at **both** the application layer and the database-query layer. A valid login must never imply access to every workspace.

### Account creation

Controlled registration or an initial-administrator bootstrap flow. Public self-registration is **not** enabled by default.

## Release gate

Authentication is not complete until cross-workspace access tests prove that one workspace cannot read or modify another workspace's data.

## Consequences

- Argon2id is not in the Python standard library (`hashlib` offers scrypt and PBKDF2), so a dependency will be needed. Per `AGENTS.md` it must be justified when added; the library choice is made at implementation time and needs registry access (D-09).
- Server-side sessions add a database read per authenticated request; acceptable for the baseline, revisited only under ADR-0001's triggers.
- Federated login (SSO/OIDC) would need a new ADR.

## Implementation notes (proposed — not part of the decision)

- Store only a hash of the session token in the database, so a database leak does not yield usable sessions.
- Choose and document the CSRF mechanism (for example a synchronizer token) when implementing; the memo requires CSRF protection but does not select one.
- Rate-limit and audit failed logins; the mechanism must not require Redis.

## Ranked implementation sequence

1. Record this decision (this ADR).
2. Users, workspaces and memberships.
3. Password hashing, login, logout and session revocation.
4. Workspace-scoped authorization and isolation tests.
5. Audit events for identity and permission changes.
6. PostgreSQL-backed background jobs.
7. Frontend integration.
8. CI, integration tests and deployment validation once registry access is restored.

Steps 2–8 are **not started**.
