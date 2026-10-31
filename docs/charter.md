# NMI Project Charter

## Project

NICEONE Marketing Intelligence (NMI)

## Mission

Establish and grow an independent, standalone marketing-intelligence application, built on a sound engineering foundation and delivered in phases under the approved 16-phase implementation roadmap.

## Independence requirement

NMI is a standalone application. It must not:

- import code from OIS, USIE, OCIF, NICEONE Agent Weave or any other NICEONE application;
- use their runtime services;
- share databases with them;
- depend on their credentials;
- require integrations with them.

Future integrations must use documented, versioned external interfaces, approved by the product owner.

## Scope of the current assignment

Phase 0 (repository inspection and governance) and Phase 1 (engineering foundation) only. Later phases are out of scope until both exit gates pass.

## Out of scope (until explicitly approved)

- Scraping or automated collection from third-party platforms.
- Any access-control bypass.
- Microservices or additional deployable units.
- Any integration with other NICEONE applications.

## Roles

- **Product owner** — approves scope, data sources, integrations and the decisions listed in `decisions-pending.md`.
- **Coding agent** — implements the assigned phase under `AGENTS.md`, reports honestly, and stops at exit gates.

## Success criteria for Phases 0–1

See the exit gates in `docs/roadmap.md`.
