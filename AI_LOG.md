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

### 2026-10-15 — Full classification run and quote-grounding repairs
- Tool / model: Claude Code (Opus 5.5); classifier claude-haiku-4-5-20251001 (owner-run).
- Task: the owner ran `make classify` on all 813 judgments (100-judgment pilot first): 0 schema failures, 0 truncated, about 2.1 M tokens. 118 of 695 relevant quotes (17 %) were rejected by grounding, 10 of the pilot's 13 on test questions q6/q7. Diagnosed offline from the recorded answers: the model joined passages with "...", left out paragraph numbers ("II –"), wrote straight for curly quotes, mended spacing/hyphenation broken in the source ("promes-sa", "contratopromessa"), added a final full stop, or exceeded 400 characters.
- Prompt / approach: kept prompt `classify_v1` (frozen; rewording after seeing answers on test questions would be tuning on results, rule 8, and would mean paying for the run again). Instead `grounding.ground` locates the quote with the named repairs in SPEC §6.1 and stores the text's own span; `is_grounded` (whitespace-only) still gates every stored quote and `make data-check` re-checks it. `--reground` re-applies grounding from the replay fixtures with no API calls.
- What failed or needed correction: grounding compared the model's string verbatim, so faithful quotes with trivial differences were discarded and their positions lost. First attempt left 31 rejections; inspecting them showed source-text defects and "[...]", so a spacing/hyphen-insensitive fallback, bracketed ellipsis and trailing-stop rules were added.
- How it was fixed: after re-grounding 11 rejected, 684 accepted (577 exact, 22 typography, 25 numbering, 9 spacing, 4 punctuation, 23 ellipsis = longest piece only, 41 trimmed at a sentence end; a quote can count in more than one). The 11 left are real misquotes (paraphrase, text not in the sumário, "codigo" for "código"). Limits to disclose: ellipsis and trimmed quotes show only part of what the model cited, so the shown excerpt may support the position less clearly. Database backed up to `data/juris.before-reground.db` first. `make detect`: 25 divergences, 20 split/shift on test questions.
- Rule 8 (no tuning on results): the repairs were designed in two rounds after inspecting rejections that were mostly on test questions, and they change the input to Gate G3, so this is stated plainly. Evidence they do not favour a position: no repair reads `position_id`, and the position ratios barely move (pilot + full run before → after re-grounding): q6 absoluto:relativo 30:82 → 43:112; q7 detentor:possuidor 35:48 → 46:61; q8 exige:não exige 17:17 → 21:18; q9 não prevalece:prevalece 12:17 → 13:21; q10 admissível:afastada 16:12 → 18:13. Of the 46 quotes the judge will see (23 split/shift pairs), 39 are exact and 5 are partial (3 trimmed, 2 longest-piece-of-ellipsis), which if anything biases the judge towards "no real opposition". `make export` + `make data-check` on the real database: 0 errors with grounding.
- Human verification (what was checked by a person): none yet; the judge pass and the evaluation against the 60 labels follow.

### 2026-10-15 — Optional workspace header for keys not scoped to a workspace
- Tool / model: Claude Code (Opus 5.5)
- Task: the pilot re-run now showed the cause: "This API key is not scoped to a workspace, so this request must include the anthropic-workspace-id header". Added an optional `LLM_WORKSPACE_ID` env var; when set, `make classify` and `make judge` send it as `anthropic-workspace-id`. Documented in `.env.example` and runbook §1.
- What failed or needed correction: the provider assumed a workspace-scoped key.
- How it was fixed: as above; a unit test checks the header is sent only when set.
- Human verification (what was checked by a person): pending; the owner re-runs the pilot.

### 2026-10-15 — Show the API's error message on a failed live call
- Tool / model: Claude Code (Opus 5.5)
- Task: the owner's first `make classify ARGS="--pilot 100"` failed with a bare `400 Bad Request` traceback, which does not say why. `AnthropicProvider` now raises `ApiError` carrying the API's own error type and message (the response body never contains the key); `make classify` and `make judge` print it and exit without a traceback. Runbook §5 lists the usual 400 causes (no credit, wrong model name).
- What failed or needed correction: `raise_for_status()` dropped the response body, so the cause of the 400 was lost.
- How it was fixed: as above, with a unit test using a mocked 400 response.
- Human verification (what was checked by a person): pending; the owner re-runs the pilot and reads the message.

### 2026-10-15 — Evaluation labels (60 rows) filled by AI, not by a human
- Tool / model: Claude Code (Opus 5.5)
- Task: fill `data/eval/labels.csv` from `data/labelling/sheet.md` (ROADMAP M3, a `HUMAN:` task). The owner had no time and no legal training and asked the agent to do it; the agent first declined, then did it on explicit owner instruction.
- Prompt / approach: read each sumário only (no model output exists yet, no dgsi.pt access); one label per row; `unclear` when the sumário distinguishes cases or decides only the concrete case; reasons in `notes`.
- What failed or needed correction: nothing technical. Methodological limits: (1) the gold labels are not human; (2) labeller and classifier are both Claude models, so errors may be correlated and agreement inflated; (3) no legal expert reviewed them. Result: 60 labels (29 position labels, 29 nao_decide, 2 unclear).
- How it was fixed: disclosed in `data/eval/labeller.md`; must be stated in `data/eval/report.md` and `IA.md`. The labels are still blind to the classifier (committed before any classification run).
- Human verification (what was checked by a person): none. A jurist's review of the 29 position labels and the 2 `unclear` rows is recommended.

### 2026-10-15 — Cost guards for the live run
- Tool / model: Claude Code (Opus 5.5)
- Task: on the owner's request, bound the worst-case API cost. Changes: answers capped at 1 200 tokens (was 2 000); an answer cut at the cap (`stop_reason=max_tokens`) is not retried; `make classify` stops at a token budget (default 3 M, about 2x the estimate) and prints progress every 50 judgments; the judge treats a cut answer as invalid instead of crashing.
- Prompt / approach (one line): the run is resumable, so stopping on budget loses nothing.
- What failed or needed correction: the first version retried truncated answers, which would pay twice for the same cut-off output.
- How it was fixed: a separate `Truncated` exception that the retry loop does not catch. Tests use a mock HTTP transport for the truncation case and for budget stop plus resume.
- Human verification (what was checked by a person): none yet.

### 2026-10-15 — M4 T4.2 export, data-check and minimal UI
- Tool / model: Claude Code (Opus 5.5)
- Task: `juris/export/` (pydantic schemas, deterministic `make export`, `make data-check` added to CI) and the web app routes `/`, `/perguntas`, `/perguntas/:id` (hand-rolled SVG timeline, no d3 dependency; Okabe-Ito colours plus a marker shape per position; divergence cards; judgments table as the chart's data-table alternative).
- Prompt / approach (one line): publish only grounded quotes ≤ 400 characters and links; a split/shift is published only with a confirming judge verdict (unjudged/hidden become counts); quotes rendered as text, never HTML.
- What failed or needed correction: the existing tests rendered `<App />` without a router; they were wrapped in `MemoryRouter`, and the disclaimer regression now checks every route. There was an act() warning in one test, and the rule confidence showed "media" without the accent.
- How it was fixed: tests are async; the confidence labels are in `messages.pt.ts`. 3 Python tests (export filters, determinism and an empty database, data-check catching bad links, long quotes and ungrounded quotes) and 10 web tests. Visual check: built the site, served it with `vite preview` using the export-test data, and took a screenshot of `/perguntas/q6` in Chrome. The only console error was a 404 for the missing favicon.
- Human verification (what was checked by a person): none yet. The live site stays empty until the owner classifies and exports.

### 2026-10-15 — M5 T5.2 judge pass and LLM runbook
- Tool / model: Claude Code (Opus 5.5)
- Task: `juris/detect/judge.py`. The judge pass sees only the question, the two quotes, their dates and assigned positions (SPEC §6.4), covering at most 40 divergences, weakest-side support first. It adds rule confidence (§6.5), the UI label rule, and the Gate G3 verdict. Also `make judge` / `make judge-replay`, and `docs/llm-runbook.md` for the owner (key, spend limit, env vars, order, cost estimate).
- Prompt / approach (one line): verdicts are cached as replay fixtures (replay first, live on a miss), so rerunning detect and the judge does not pay twice.
- What failed or needed correction: a `
` inside an f-string became a literal line break when generated through a script (syntax error). On an empty database the gate printed "PIVOT", which is misleading before any classification exists.
- Review fix (same day, before any judge run): the first version showed the judge each excerpt's assigned position. SPEC §6.4 gives the judge only the quotes, the dates and the question, and the labels would prime it toward confirming, which biases Gate G3. Removed from the input and the prompt.
- How it was fixed: rewritten; the gate now says it is not decidable while nothing is classified. 8 new unit tests (rule confidence, ranking, display, gate counting test questions only, cache).
- Human verification (what was checked by a person): none yet.

### 2026-10-15 — M5 T5.1 detection
- Tool / model: Claude Code (Opus 5.5)
- Task: `pipeline/juris/detect/` (pure functions for split, shift and resolved, plus the uniformização marker), `detect.toml` with the SPEC §6.2 defaults, and `make detect` writing the `divergence` table. Written before any classification exists, so nothing was tuned on results.
- Prompt / approach (one line): SPEC §6.2 leaves open how overlapping windows count; chosen: merge overlapping split windows, one shift per change of dominant position, a dominant position also needs `k`, ties have none. Recorded in SPEC §6.2.
- What failed or needed correction: 5 of my first test expectations were wrong, not the code. Window spans were off by a year (a 2010–2011 split lights up windows 2009–2012), and a case I called "flicker" (A in 2005, B in 2007) is a real shift under the SPEC definition. The split-pair code was first written convolutedly and was simplified.
- How it was fixed: expectations recomputed by hand and the test renamed (`test_adjacent_periods_count_as_a_shift`); 12 tests on synthetic data plus a database test. `make detect` on the real database prints 0 divergences, as expected with no classifications yet.
- Human verification (what was checked by a person): none yet.

### 2026-10-15 — Gate G3 fixed before results
- Tool / model: Claude Code (Opus 5.5)
- Task: record the owner's pivot rule (SPEC §2 Gate G3, ROADMAP M5) before any classification exists, per AGENTS.md rule 8.
- Prompt / approach (one line): options offered: ≥ 1 or ≥ 2 judge-confirmed divergences, or never pivot; the owner chose ≥ 1 on a test question.
- What failed or needed correction: nothing.
- How it was fixed: n/a.
- Human verification (what was checked by a person): the owner chose the rule.

### 2026-10-15 — M4 T4.1 classification module
- Tool / model: Claude Code (Opus 5.5)
- Task: `juris/llm/provider.py` (provider interface, ReplayProvider keyed by sha256 of the canonical request, Anthropic adapter over `httpx` with temperature 0, cached system block and a replay fixture recorded per answer); `juris/classify/schema.py` (pydantic validation of the untrusted answer against the approved questions); `juris/classify/run.py` + `__main__` (sumário first per ADR 0007, one retry on schema failure only, grounding check against the text actually sent, resume by prompt version, stratified `--pilot`).
- Prompt / approach (one line): no new dependency; the live run refuses to start until all 60 blind labels are filled (`--not-blind` overrides), so model output cannot precede the labels.
- What failed or needed correction: two lines over the ruff limit. SPEC §7's `generate_json(prompt_id, input)` had no place for the rendered prompt, so the signature gained `system`.
- How it was fixed: wrapped; SPEC §7 updated. Unit tests cover the schema, grounding rejection, the text fallback, resume, the retry, the HTTP adapter (mock transport) and the label guard. `make classify-replay` was smoke-run on the real database: 0 fixtures exist yet, as expected.
- Human verification (what was checked by a person): none yet. The live pilot (`make classify ARGS="--pilot 100"`) is HUMAN-run after the labels are committed.

### 2026-10-15 — Taxonomy frozen (v1) and blind label sheet (M3 T3.3)
- Tool / model: Claude Code (Opus 5.5)
- Task: freeze the taxonomy (`v1`) and the classification prompt (`pipeline/juris/llm/prompts/classify_v1.md`, rendered by `juris/llm/prompt.py` with approved questions only), and generate the 60-row blind label sheet (`pipeline/tools/labelsheet.py`). Owner decisions taken before any model output: the model classifies from the sumário (ADR 0007, amends ADR 0006), and the dev set is q2 + q3 (SPEC §9.7).
- Prompt / approach (one line): fixed keyword pools per approved question, 8–9 rows each, evenly spaced by date, excluding the 195 judgments already shown to the owner with an LLM answer (spike, discovery); sheet with sumários is local (`data/labelling/`, gitignored), `data/eval/labels.csv` holds ids and empty labels only.
- What failed or needed correction: SPEC §9.1 said "12 per seed question", but only 2 of the 5 seeds were approved, and ROADMAP T7.1 said discovered questions are not evaluated. Both were rewritten for the 7 approved questions before generating the sheet. The earlier `render_questions` in the discovery tool also renders rejected questions; the classification prompt uses its own renderer that keeps only `approved`. One test expectation was wrong (Python rounds 12.5 to 12).
- How it was fixed: SPEC §6.1, §9.1 and §9.7, ROADMAP T3.3/T7.1 updated; ADR 0007 added; tests for the allocation, exclusion, label validation and the approved-only prompt.
- Human verification (what was checked by a person): owner read and accepted the q6–q10 position definitions and chose the model input and the dev split. Pending: owner labels the 60 rows from the sumário and records their legal background in `data/eval/labeller.md`.

### 2026-10-15 — Taxonomy approved (7 questions)
- Tool / model: Claude Code (Sonnet 5.5)
- Task: write the approved `data/taxonomy.json` from the owner's decision on the discovery results: approved q2, q3 (kept for the survey comparison), q6 prazo absoluto/relativo, q7 possuidor/detentor, q8 retenção exige consumidor, q9 retenção vs hipoteca, q10 sinal e execução específica; rejected q1, q4, q5.
- What failed or needed correction: before writing the position definitions I re-read the quotes: for q10 both found judgments (2008, 2013) sit on the same side, so it is not yet two-sided as I had first presented it; kept because the full classification will show whether the other side exists. Position definitions are drafted from the quotes, not checked by a lawyer.
- How it was fixed: stated in the seed_source of q10; test now checks the approved ids. Note for M4: classification must use only `status == "approved"` questions (the discovery packs rendered all of them).
- Human verification: the owner chose the list; still pending: read the position definitions of q6-q10.

### 2026-10-14 — M3 discovery pass result (150 judgments)
- Tool / model: owner ran the 3 packs in an LLM chat (human-run); Claude Code (Sonnet 5.5) ran `discovery.py check` and read the output.
- Task: gate G2 measurement and new-question proposals.
- What failed or needed correction: 0 of the 150 sumários had a quote rejected. The five seed questions show no split: q1 1 position (1 judgment), q2 only basta_mora (4), q3 only exige_definitivo (7), q4 and q5 nothing. The tool printed "10 proposed questions with >= 2 positions", but that count is inflated: position labels are free text, so near-identical labels ("pressupõe resolução" / "pressupõe resolução, implícita no pedido") count as two positions. After merging by hand, about 5 questions look like real two-sided cases (prazo absoluto/relativo, possuidor/detentor, retenção exige consumidor, retenção vs hipoteca, sinal e execução específica), each with only 1-3 judgments on the minority side.
- How it was fixed: `check` now also prints the years behind each label. The G2 criterion was not changed; the owner decides which proposed questions to approve.
- Human verification: pending (owner approves, edits or rejects the questions).

### 2026-10-14 — Taxonomy: allow 2-4 positions per question
- Tool / model: Claude Code (Sonnet 5.5)
- Task: owner asked why a question may have at most 3 positions; relaxed to 4 in the validator and SPEC §5.1, with a test.
- What failed or needed correction: the limit was a SPEC choice I had enforced as written, not a detection requirement (split/shift/resolved work with any number of positions).
- How it was fixed: `2 <= positions <= 4`; tradeoff noted (labelling accuracy, UI readability).
- Human verification: the owner made the decision.

### 2026-10-14 — M3 start: seed taxonomy and discovery pass kit
- Tool / model: Claude Code (Sonnet 5.5)
- Task: T3.1 `data/taxonomy.json` (5 seed questions from SPEC §5.2) with a pydantic loader/validator; T3.2 kit for the discovery pass: `pipeline/tools/discovery.py pack|check`, prompt `discovery_v0.md`, 150 random judgments (stratified by year, seed 20261015) in 3 packs of 50.
- What failed or needed correction: a long shell heredoc failed to parse again and wrote nothing (files then written with the file tool). `data/discovery/` was not gitignored although it holds sumários; caught before committing and added to `.gitignore`.
- How it was fixed: as above. `check` verifies every quote against the stored sumário and prints positions per seed question (gate G2) plus the proposed new questions. The position wording of q4 and q5 is my draft from the survey summary, not checked by a lawyer; owner approval is the T3.2 HUMAN step.
- Human verification: pending. The owner runs the three packs in an LLM chat, saves answer_1..3.json, runs `check`, and approves, edits or rejects the questions and positions.

### 2026-10-14 — M1.5 spike result (questions 1 and 2)
- Tool / model: owner ran both packs in an LLM chat (human-run); Claude Code (Sonnet 5.5) ran `spike.py check -q q1|q2` and read the notes.
- Task: check quotes and count positions for seed questions 1 and 2 on the full fetched pool.
- What failed or needed correction: both fail the criterion (at least 2 positions). Q1: 1 A, 19 nenhuma; the keyword filter (execução específica + alienação/terceiro/eficácia real) mostly caught judgments on other points (insolvência, penhora, propriedade horizontal), so Q1 is not really tested. Q2: 6 A, 0 B. 0 invented quotes in both. Positions are read from sumários only.
- How it was fixed: not a code problem; criterion not changed. Options put to the owner: go on to the M3 discovery pass (G2), tighten the Q1 filter, or switch to the fallback subset.
- Human verification: pending (owner reads a few sumários, in particular Q2 judgments from 2008–2013 that the survey cites).

### 2026-10-14 — M1.5 spike kit for questions 1 and 2
- Tool / model: Claude Code (Sonnet 5.5)
- Task: generalise `pipeline/tools/spike.py` to `-q q1|q2|q3` (per-question pack and ids files) and write draft prompts `spike_q1_v0.md` (execução específica vs alienação a terceiro) and `spike_q2_v0.md` (mora vs incumprimento definitivo).
- What failed or needed correction: nothing failed. Candidate keywords were fixed before any model output (full pool of 810 fetched: q1 38 candidates, q2 59, q3 161). The position wording for q1/q2 is my neutral draft from SPEC §5.2, not checked by a lawyer.
- How it was fixed: n/a.
- Human verification: pending. The owner should read the two position definitions in the prompts, run the packs in an LLM chat and run `check`.

### 2026-10-14 — Full `make fetch`: 3 processo mismatches
- Tool / model: Claude Code (Sonnet 5.5)
- Task: read the owner's last `make fetch` output (3 left of 813, all FAILED with `processo mismatch: index '04S4759' vs '04S4759ver acórdão T REL'`).
- What failed or needed correction: parser bug, not a site problem. On some pages the Processo cell holds a nested table with the number plus a link "ver acórdão T REL" (the related Relação judgment), and `cell_text` joined both. The safety check against the index row caught it, so nothing wrong was stored.
- How it was fixed: `_processo_text` takes only the first cell of the nested table; unit test on a synthetic page; all cached pages with such a link re-parse to the plain number. The 3 rows are in the cache, so re-running `make fetch` stores them with 0 requests.
- Human verification: pending; the owner re-runs `make fetch` and confirms 0 failures.

### 2026-10-14 — M1.5 spike result (question 3)
- Tool / model: owner ran the pack in an LLM chat (human-run, per AGENTS.md); Claude Code (Sonnet 5.5) ran `spike.py check` and read the answers.
- Task: classify 20 pilot sumários on "sinal e mora" and verify the quotes.
- What failed or needed correction: criterion failed: only position B (9), no A, 11 "nenhuma". The 11 are off-question or silent per the model's notes (interpelação admonitória, tu quoque, direito de retenção, insolvência). No invented quotes (0 of 9 rejected). A forked agent correctly refused to answer the pack itself (HUMAN task).
- How it was fixed: not a code problem. Result recorded in ROADMAP M1.5; next step is a larger pool (fetch the rest of the subset) and questions 1 and 2, not an immediate subset switch, because one question over 20 keyword-picked sumários is weak evidence. The pass criterion was not changed after seeing the result.
- Human verification: pending; the owner should read the sumários of judgments 1, 2, 11 and 15 and say whether the model's B reading is right.

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
