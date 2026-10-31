# Superseded Sections of the Original Specification

The original `niceone_marketing_intelligence_spec.md` (held in the Project docs, **not modified**) conflicts with accepted decisions in several places. Where they differ, the accepted decisions below govern. Resolves D-11.

| Spec section | What it says | Status | Governing decision |
|---|---|---|---|
| §3.1, §5.1 | Redis as broker with Dramatiq/Celery workers | **Superseded** | ADR-0001: PostgreSQL-backed jobs; Redis deferred |
| §5.2 | MinIO / S3-compatible object storage for blobs | **Superseded** | ADR-0001: local filesystem behind a storage interface; MinIO deferred |
| §3.2 "Infrastructure" | Caching layers and task routing | **Superseded** (caching) | ADR-0001: no Redis cache in Phase 1 |
| §4, §4.2 | Bright Data / Apify proxy-rotation fallback after network blocks | **Superseded** | Collection policy below |
| §4.1 | Scrapy, Bright Data, Apify as baseline ingestion vectors | **Superseded as baseline** | Project plan §4: add a provider only when a documented gap justifies it |

## Collection policy (retained)

Use official APIs, approved integrations, authorized browser sessions, permitted public sources and user-provided files. Do **not** bypass authentication, CAPTCHAs, paywalls, platform access controls or anti-bot protections (including via proxy rotation). Record unavailable or restricted fields as unavailable; never fabricate them. Any data-source integration needs written product-owner approval before implementation.

None of the superseded mechanisms are implemented in this repository.
