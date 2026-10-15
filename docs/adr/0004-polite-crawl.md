# ADR 0004 — Polite-crawl policy

Status: accepted (2026-10-12). Recorded retroactively on 2026-10-15; the rules are in SPEC §3 and AGENTS.md rules 1–2.

## Context
dgsi.pt is a public service with no robots.txt (checked by the owner on 2026-10-12). Having no robots.txt is not permission, and the crawl must cost the site as little as possible.

## Decision
- One connection and one request at a time, with at least 2.5 s (plus 0–1 s jitter) between requests and a 30 s timeout.
- An identifying `User-Agent` that carries the owner's contact (`JURIS_CONTACT`).
- Every response is cached on disk (`data/raw/`, gitignored) by canonical URL. No URL is requested twice, and runs resume from the cache.
- A run stops at the first HTTP 429/503 or after 3 consecutive errors. There are no retry loops and no workarounds. Each run has a request cap (`--max-requests`, default 800) and runs off-peak.
- A host allowlist is checked before every request.
- Only a person runs `make index` and `make fetch`. AI agents never contact dgsi.pt and work from saved fixtures.

## Consequences
- The full index takes about 740 requests (about 40 min). With the subset's documents, the whole crawl is about 1.3–2.5 h.
- Tests run offline on HTML fixtures in `pipeline/tests/fixtures/`.
