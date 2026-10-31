# AGENTS.md — Operating rules for coding agents on NMI

NICEONE Marketing Intelligence (NMI) is a **standalone** application. These rules apply to every coding agent (and human) changing this repository.

## 1. Independence (non-negotiable)

- Do not import code from, call at runtime, share a database with, borrow credentials from, or require integrations with OIS, USIE, OCIF, NICEONE Agent Weave or any other NICEONE application.
- Future integrations happen only through documented, versioned external interfaces approved by the product owner (see `docs/decisions-pending.md`).

## 2. Scope discipline

- Work only on the phase assigned in `docs/task-register.md`. Do not start the next phase until the current phase's exit gate is recorded as passed in `docs/reports/`.
- Do not commit unrelated changes. One concern per commit.
- Do not add platform scraping, data collection from third-party platforms, or any access-control bypass. Any data-source integration needs written product-owner approval first.

## 3. Git safety

- Never rewrite shared history (no force-push, no rebase of pushed commits, no `reset --hard` of shared branches).
- Never delete or overwrite existing user work. Inspect `git status` before changing anything; if the tree is dirty with changes you did not make, stop and report.
- Work on a feature branch; never commit directly to `main`.

## 4. Architecture

- Modular monolith: one deployable backend (`backend/`), one frontend (`frontend/`). No new services or microservices without an approved decision.
- Backend code lives in `backend/app/modules/<domain>/`. A module exposes its public surface through its `api.py` router and `service.py`; other modules must not reach into its internals. Cross-cutting infrastructure lives in `backend/app/core/` and `backend/app/platform/`.
- Prefer typed interfaces and validated schemas (Pydantic models, strict mypy, TypeScript `strict`).
- Every database change goes through an Alembic migration. Never edit a migration that has been merged; add a new one.

## 5. Dependencies

- Add a dependency only when the standard library or an existing dependency cannot reasonably do the job. State the reason in the commit message.
- Lock files (`backend/uv.lock`, `frontend/package-lock.json`) are committed and must be updated together with manifests.

## 6. Secrets

- No secrets in source control, docs, tests or logs. `.env` is git-ignored; `.env.example` holds placeholders only.
- Configuration is validated at startup. Outside `local`/`test`, placeholder or weak secrets must make the app refuse to start.

## 7. Quality gates (run before every commit)

Backend (from `backend/`):

```
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest
```

Frontend (from `frontend/`):

```
npm run lint
npm run typecheck
npm test
npm run build
```

## 8. Honesty about results

- Never fabricate or paraphrase-away test output. Report commands actually run and their actual results.
- If something could not be run (for example, Docker or CI in a restricted environment), say so explicitly in the phase report under known limitations.

## 9. Documentation

- Update `docs/task-register.md` and `docs/risk-register.md` as work completes or risks change.
- Decisions that need the product owner go in `docs/decisions-pending.md`; do not decide them unilaterally.
