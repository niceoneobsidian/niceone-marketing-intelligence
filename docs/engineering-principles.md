# Engineering Principles

1. **Modular monolith.** One backend deployable, explicit domain modules, no unnecessary microservices.
2. **Explicit boundaries.** Modules interact through their public `api`/`service` surface only. Infrastructure is isolated in `core/` and `platform/`.
3. **Typed and validated.** Pydantic schemas at the edges, strict mypy in the backend, TypeScript `strict` in the frontend.
4. **Secrets stay out of source control.** Configuration comes from the environment, is validated at startup, and weak or placeholder secrets are rejected outside `local`/`test`.
5. **Migrations for every schema change.** Alembic is the only way the schema changes.
6. **Tests alongside implementation.** Behaviour ships with tests. Test results are reported as run, never fabricated.
7. **Minimal dependencies.** Add one only when the standard library or an existing dependency cannot do the job.
8. **Reproducible environments.** Locked dependencies, Docker Compose for local services, CI that runs the same checks as developers.
9. **Observable by default.** Structured JSON logs with a request ID; separate liveness and readiness endpoints.
10. **No unapproved data collection.** No platform scraping and no access-control bypasses.
11. **Small, focused changes.** Unrelated changes are never committed together.
