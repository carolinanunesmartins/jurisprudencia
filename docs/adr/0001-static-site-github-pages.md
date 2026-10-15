# ADR 0001 — Static site on GitHub Pages

Status: accepted (2026-10-12). Recorded retroactively on 2026-10-15; the decision is in SPEC §8 and §12.

## Context
The output is a read-only view of a fixed, published dataset. SPEC §1 rules out search, chat/RAG and accounts, so nothing needs a server at request time.

## Decision
- Vite + React + TypeScript build to static files. The pipeline writes `web/public/data/*.json` (`make export`), and the site only reads them.
- HashRouter, so every route works on a host without server rewrites.
- Hosting on GitHub Pages, deployed by GitHub Actions after `make data-check` passes (`.github/workflows/deploy.yml`).
- Security headers cannot be set on Pages, so the CSP is a `<meta http-equiv>` in `web/index.html` (`frame-ancestors` is not enforceable there).

## Consequences
- No backend, cookies or analytics, and no request leaves the site's origin.
- Hash routes are not indexed separately by search engines.
- A Pages project site cannot serve `robots.txt` at the origin root.
