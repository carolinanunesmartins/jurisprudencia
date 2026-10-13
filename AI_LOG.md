# AI_LOG.md

Living record of how AI tools were used in this project. It is the source for `IA.md` (ROADMAP M8).
**Keep it up to date: every change made with AI assistance needs an entry in the same PR** (AGENTS.md §4 rule 11).

## Entry format (newest first)
```
### YYYY-MM-DD — <short title>
- Tool / model:
- Task:
- Prompt / approach (one line):
- What failed or needed correction:
- How it was fixed:
- Human verification (what was checked by a person):
```

---

### 2026-10-13 — M1 crawler core and DB schema
- Tool / model: Claude Code (Sonnet 5.5)
- Task: SPEC §3 polite fetcher (delay, cache, stop rules, host allowlist, request cap) with tests on httpx.MockTransport; SQLite schema from SPEC §4.
- What failed or needed correction: (1) a very long shell heredoc command failed to parse, nothing was written; (2) the first `canonical_url` re-encoded the query and turned `?OpenDocument` into `?OpenDocument=`, caught by a unit test.
- How it was fixed: wrote files with the file tool; canonical_url now filters raw query segments. Added a regression golden file for it.
- Human verification: pending. The fetcher has never run against the real site (agents must not); the owner should check the first live run against SPEC §3.

### 2026-10-12 — GitHub Pages deploy and README
- Tool / model: Claude Code (Sonnet 5.5)
- Task: switch deploy workflow from Cloudflare to GitHub Pages (SHA-pinned actions, CSP via meta tag), rewrite README in pt-PT.
- What failed or needed correction: `make` on this machine resolved to the npm package `make` (v0.8.1), not GNU Make, and `uv` was not on PATH in the session, so `make verify` could not be run here.
- How it was fixed: documented the distinction in the README; verification left to the owner / CI.
- Human verification: pending (owner to run `make verify`, enable Pages, check the CI run).

### 2026-10-12 — Scope/roadmap review and edits
- Tool / model: Claude Code (Sonnet 5.5)
- Task: analyse SPEC/ROADMAP against the project goal; apply agreed improvements (feasibility spike, stratified pilot, earlier labelling, committed classification snapshot, buffer note).
- What failed or needed correction: original brief not available to the model, so the review could not check against the test's evaluation criteria.
- How it was fixed: stated as a limitation; owner to compare against the brief.
- Human verification: pending (owner to read the ROADMAP/SPEC diff).

### 2026-10-12 — Repo scaffold
- Tool / model: Claude Code (Sonnet 5.5)
- Task: read SPEC/ROADMAP/AGENTS, clone the repo, create AI_LOG.md, project structure, unit + regression test layout, CI workflows.
- Prompt / approach: single instruction asking for a starting structure to extend later.
- What failed or needed correction: `git clone` cannot target a non-empty folder; `uv` and `make` are not installed on this machine, so the Python side and Makefile were not executed here.
- How it was fixed: used `git init` + `fetch` + `checkout` to attach the existing files to `origin/main`.
- Human verification: pending (owner to run `make setup && make verify`).
