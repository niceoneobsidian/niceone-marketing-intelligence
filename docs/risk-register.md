# Risk Register

Likelihood / impact: L = low, M = medium, H = high. Status: `open`, `mitigated`, `accepted`, `closed`.

| ID | Risk | L | I | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|
| R-01 | The governing roadmap is unclear (directive says 16 phases; the project plan defines P0–P11 as a proposed baseline), so phase boundaries may drift. | H | M | Product owner confirms which roadmap governs (D-01). | Product owner | open |
| R-02 | No canonical remote repository was reachable; work exists only locally and could be lost or diverge from the real repo. | M | H | Identify repo (D-02); push the branch and open a PR once access exists. | Product owner | open |
| R-03 | Docker daemon unavailable in the build environment, so the Compose file (PostgreSQL only) was validated with `docker compose config` but never run. | M | M | First `docker compose up` by a developer or CI before relying on it. | Engineering | open |
| R-04 | CI workflow could not be executed in the build environment; it is verified only by static checks until pushed. | M | M | Push branch and confirm the first CI run; record result. | Engineering | open |
| R-05 | Weak or placeholder secrets reaching staging/production. | L | H | Startup validation and unit tests are written but have never been run (R-11). Becomes `mitigated` only after the tests pass. | Engineering | open |
| R-06 | Scope creep into scraping or data collection from third-party platforms. | L | H | Prohibited in `AGENTS.md`; requires approved data-source policy (D-07). | Product owner | open |
| R-07 | Dependency drift or supply-chain issues. | M | M | Plan: committed lock files, minimal dependencies, CI installs from locks plus dependency scanning. No lock file exists yet (R-09). | Engineering | open |
| R-09 | Package registries (pypi.org, registry.npmjs.org) are denied by the build environment's egress policy, so dependencies cannot be installed, locks cannot be generated, and no code can be run or tested. Phase 1 is blocked. | H | H | Product owner grants registry access or an approved mirror (D-09). Code written meanwhile is marked unverified in the task register. | Product owner | open |
| R-08 | Accidental coupling to other NICEONE applications. | L | H | Independence rule in `AGENTS.md` and charter; review for cross-app imports. | Engineering | open |
| R-10 | The original spec and the project plan disagree (Redis/MinIO; Bright Data/Apify proxy rotation vs the no-circumvention collection policy). Implementers could follow the wrong document. | M | H | ADR-0001 supersedes the Redis/MinIO parts; reconcile the spec (D-11). Nothing conflicting is implemented. | Product owner | open |
| R-11 | Security-sensitive and stateful code (storage, config validation, readiness) was written without any ability to run it. It may contain defects. | H | M | Treated as unverified in the task register; full checks, integration tests and review once registries are reachable (D-09). | Engineering | open |
