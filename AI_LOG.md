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

### 2026-10-14 — Repo hygiene and security review
- Tool / model: Claude Code (Sonnet 5.5), `/security-review` with a hygiene brief.
- Task: look for loose env files, committed secrets or data, missing ignores and stale files; review the branch diff for vulnerabilities.
- What failed or needed correction: `data/*.db` did not cover SQLite sidecar files (`-journal`, `-wal`, `-shm`), which can hold judgment text and would break AGENTS.md rule 3 if added by accident. Local tool settings and editor/OS files were also not ignored. `docs/adr/.gitkeep` was stale.
- How it was fixed: added the ignore patterns and removed the `.gitkeep`. Checked tracked files, history and content: no `.env`, keys, tokens, databases, cache or personal paths were ever committed; no code vulnerabilities found (SQL is parameterised, the crawler host is allow-listed, cache file names are hashes).
- Human verification: pending; the owner should confirm GitHub secret scanning stays enabled.

### 2026-10-14 — M1.5 spike kit
- Tool / model: Claude Code (Sonnet 5.5)
- Task: choose spike judgments from the pilot, write the draft prompt (`pipeline/juris/llm/prompts/spike_q3_v0.md`, seed question 3: sinal e mora) and a `pack`/`check` tool that builds the paste-in file and verifies the model's quotes against the stored sumário.
- What failed or needed correction: nothing yet; the model pass has not run. Choice made without results: question 3 because the pilot has 23 sumários mentioning sinal plus mora/definitivo across 2002–2025, against 4–5 for questions 1 and 2. The pass criterion is ROADMAP's (at least 2 positions observed); the report also prints the support per position.
- How it was fixed: n/a.
- Human verification: pending. The owner runs the prompt in an LLM chat, saves the JSON answer and runs `check`; the owner should also read a few of the 20 sumários to judge whether the model's positions are right.

### 2026-10-14 — Pilot completed: 91% complete, gaps are on the site
- Tool / model: Claude Code (Sonnet 5.5)
- Task: read the owner's resume output (37 stored, 7 incomplete) and classify all 9 incomplete pilot rows from the DB and cached HTML (no network).
- What failed or needed correction: the acceptance bar (≥95% with sumário and texto) is missed: 91/100. I first suspected the parser; the cached pages show an empty "Decisão Texto Integral" cell (7 rows) or an empty "Sumário" (2 rows from 2003), so the data is missing at the source. Gaps concentrate in 2000–2003 (7 of 13 judgments) and two 2010 rows.
- How it was fixed: nothing to fix in code; the real rate is reported as ROADMAP asks, with the breakdown. The owner chose to classify sumário-only judgments from the sumário, flagged (ADR 0006, SPEC §6.1).
- Human verification: the owner made the policy decision; still pending: open one 2000–2001 judgment on dgsi.pt and confirm no full text is shown.

### 2026-10-14 — First live `make fetch` pilot run
- Tool / model: Claude Code (Sonnet 5.5)
- Task: read the owner's pilot output and inspect the two "incomplete" rows from the local cache (no network).
- What failed or needed correction: the run stopped after 63 stored because the server dropped 3 requests in a row ("Server disconnected without sending a response"). The two incomplete rows (`69/10.0YFLSB`, `3655/1998.L1.S1`, both 2010-05-20) are not a parser bug: the saved pages have an empty "Decisão Texto Integral" cell, so the site itself has no full text for them.
- How it was fixed: nothing worked around (SPEC §3 forbids it). Added `--delay` (can only be raised above 2.5 s) so the owner can be gentler on the resume. Judgments without full text must be excluded from classification in M4 (no text to ground a quote in).
- Human verification: pending. The owner should resume later and check that the two rows really show no text in the browser.

### 2026-10-14 — Review of the subset justification
- Tool / model: Claude Code (Sonnet 5.5)
- Task: explain why STJ, the descriptors, 600–1 500 judgments and 2000–2025.
- What failed or needed correction: the SPEC gives no reason for the 2000 start; the 1998 judgment cited by seed question 1 falls outside the window.
- How it was fixed: the owner chose to keep 2000–2025; the limitation is recorded in ADR 0005 (alternative 1995–2025 = 1 144 judgments).
- Human verification: the owner made the window decision.

### 2026-10-13 — Subset decision (T1.3)
- Tool / model: Claude Code (Sonnet 5.5)
- Task: from the full index, count descriptors and years, apply the SPEC §2 rule, write ADR 0005, and make `make fetch` use only the subset.
- What failed or needed correction: my first count matched descriptors by substring and was badly inflated (`EXTRADIÇÃO`, `CONTRADIÇÃO…` contain `TRADIÇÃO`; `SINALAGMÁTICO` contains `SINAL`). I also noticed that `make fetch` would have sampled the pilot from all 71 760 judgments instead of the subset.
- How it was fixed: whole-descriptor regex in `pipeline/juris/db/subset.py` with unit tests for the false positives; `fetch` restricts the pilot and the full run to the subset (`--all-index` opts out).
- Human verification: pending. The owner should skim the `[theme]`-marked descriptor list printed by `pipeline/tools/subset_counts.py` and confirm none is off-theme (for example `CONTRATO-PROMESSA DE TRABALHO`).

### 2026-10-13 — `make fetch` (M2 T2.1)
- Tool / model: Claude Code (Sonnet 5.5)
- Task: document fetch loop on top of the polite fetcher: stratified pilot sampling, resume via `fetched_at` and cache, per-document failures listed, parse results stored; tests through a mock transport on the saved judgment fixtures.
- What failed or needed correction: nothing failed; the pilot is chosen over all rows (not only pending ones) so it stays identical across interrupted runs.
- How it was fixed: n/a. Also added `ARGS` to the `fetch` Makefile target.
- Human verification: pending. Never run against the live site; the owner should run `make fetch ARGS="--pilot 100"` after the index finishes and report the failure and empty-field counts it prints.

### 2026-10-13 — `make index` live test and a key correction
- Tool / model: Claude Code (Sonnet 5.5)
- Task: implement the index crawl loop (follow "Seguinte", store rows per page, resume via cache, stop rules) and tests on the saved pages through a mock transport.
- What failed or needed correction: my first test expected 298 rows but got 297 plus a "conflict": the real saved pages show one case number (`1748/25.2T8OAZ.P1.S1`) with two different judgments, so SPEC §4's `processo` primary key was wrong.
- How it was fixed: `acordao` and `classification` are now keyed by `doc_id` (the id in the URL), `processo` is an indexed non-unique column; SPEC and ROADMAP updated; tests added for both cases. The SPEC request budget was also corrected (≈740 index requests).
- Human verification: pending. The loop has only run against saved pages; the owner should do a `--max-pages 3` live run first and compare the stored rows with the browser.

### 2026-10-13 — M1 parsers on saved fixtures
- Tool / model: Claude Code (Sonnet 5.5)
- Task: write index, judgment and descriptor-list parsers from the 8 HTML pages the owner saved; trim fixtures for committing; unit and golden tests; correct SPEC §3 facts.
- What failed or needed correction: `selectolax` default (modest) backend is deprecated and raises on import, so the lexbor backend is used; the fixtures contained full judgment texts, which AGENTS.md rule 3 forbids committing.
- How it was fixed: switched to `selectolax.lexbor`; added `pipeline/tools/trim_fixture.py` and kept the raw saves in a gitignored folder. Found that SPEC assumptions were wrong (page size about 100 not 138, `Start` values are not multiples of page size, pages overlap by one row) and updated SPEC.
- Human verification: pending. The golden JSON was checked by eye against the parsed values of the saved pages only; the owner should spot-check one judgment against the live page.

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
