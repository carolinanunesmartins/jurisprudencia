# AI_LOG.md

How AI tools were used, one entry per change, newest first. Source for `IA.md`.
**Every change made with AI assistance adds an entry in the same PR** (AGENTS.md rule 11).
Entries up to 2026-10-15 were condensed on that date; the full original wording is in commit `fea31ad`.

```
### YYYY-MM-DD — <short title>
- Tool:
- Task:
- Failed:
- Fix:
- Human check:
```

---

### 2026-10-16 — Reader-facing documents in pt-PT
- Tool: Claude Code (Opus 5.5).
- Task: owner asked that every document a reader sees be in Portuguese, internal ones in any language. Scanned every tracked `.md`: the 8 ADRs and their index, `docs/llm-runbook.md` and `CHANGELOG.md` were in English. Translated to pt-PT, file names kept so links and code references still work; the rule written into AGENTS.md (which files are pt-PT, which stay English).
- Failed: nothing.
- Fix: n/a. Facts and numbers unchanged; the runbook's section numbers kept (code points to §1 and §5).
- Human check: pending (owner reads the translations).

### 2026-10-15 — Architecture deliverable: how the MVP was built and how it continues
- Tool: Claude Code (Opus 5.5).
- Task: new deliverable `docs/arquitetura.md` (pt-PT) with Mermaid diagrams that GitHub renders: (1) the MVP in four stages (recolher, classificar, detetar, publicar); (2) the continuation, decided with the owner in two rounds of questions: for lawyers; more STJ themes, other courts, full text; scheduled incremental runs; AI-only review, disclosed; fully automatic, versioned questions; backend API + database + accounts; search by norm, ready citation, follow a question. Then a four-phase view with "ready when" criteria. README highlights it.
- Failed: the first layouts were too wide or stair-stepped (Mermaid ignores a subgraph's direction when edges cross into it); bold labels were clipped.
- Fix: stages linked subgraph to subgraph, an invisible link for side-by-side stores, shorter labels; every diagram rendered with Mermaid 11 and checked by screenshot. The risks the owner's choices bring are written next to the diagram: automatic questions drop the MVP's pre-registration, AI-only results for lawyers, personal data with accounts, cost of full text.
- Human check: owner chose every direction and approved the phase order.

### 2026-10-15 — Housekeeping, ADRs 0001–0004, security review, shorter docs
- Tool: Claude Code (Opus 5.5); `/security-review` run as a subagent over the whole repository.
- Task: review the deliverables, simplify README, IA.md and this log, remove what the repo does not need, review security.
- Failed: SPEC §11 requires ADRs for static site, supervised taxonomy, quote grounding, polite crawl and hosting, but the repo only had 0005–0008 (0001–0004 never existed). This log had grown to 9 384 words.
- Fix: 0001–0004 written from SPEC text only, marked as recorded retroactively. This log condensed: same 48 entries, the required fields kept in each, wording shortened; the template's sixth field ("prompt / approach") folded into Task. Removed the two `.gitkeep` files in non-empty folders and a stale Makefile comment. Kept the spike and discovery tools and prompts: ROADMAP M1.5/M3 and NOTA refer to them. Security: no finding at confidence ≥ 8 (React escapes all text; SQL parameterised; no shell/eval/pickle; cache and fixture file names are hashes; crawler host allow-listed; workflows read-only with SHA-pinned actions and no `pull_request_target`). Hardening: `DgsiLink` now renders a link only for `https://www.dgsi.pt/` URLs, like the deploy gate, so data that skipped the gate cannot become a `javascript:` link (regression test). 29 web tests.
- Human check: pending (owner reads the ADRs and the shortened docs).

### 2026-10-15 — Minimal reading: less text, emphasis, explanations one click away
- Tool: Claude Code (Opus 5.5); a browser-only first-time-visitor subagent judged it twice.
- Task: owner found the site a wall of text. Measured visible words per route first; then: position names bold in their colour, Mudança (filled) vs Divisão (outlined) badges, headline highlight marks, bold key numbers, evidence as bars, /metodo as stat tiles; definitions, "como foi detetada", uniformização sides, accuracy, survey and limitations behind a click. Quotes never styled; every caveat kept.
- Failed: the visitor's review found five regressions: chart legend without position names; q8 note without "o sistema não diz porquê"; "4 confirmadas" next to "2 de 3 corretas" read as a contradiction; bars not in the headline's order; uniformização cards without their question.
- Fix: all five fixed. Visible words before → after: home 421 → 314, q8 792 → 223, /uniformizacoes 888 → 259, /metodo 503 → 198, q7 detection page 314 → 119. No overflow at 360 px, light and dark. 28 web tests.
- Human check: pending (owner review on the dev server).

### 2026-10-15 — Brief verifiable at a glance; load speed and SEO
- Tool: Claude Code (Opus 5.5); first-time-visitor subagent; Lighthouse and a performance trace via Chrome DevTools MCP.
- Task: check how easily a newcomer verifies the brief (5 claims: by theme, divergences, when, where, change on the same question) and make it easier; improve speed and SEO.
- Failed: "change over time" took 3 clicks: home showed only a split, list rows said "1 divergência", a shift had no before/after and its totals (12 vs 10) read as a tie, two confidences contradicted each other, "Pergunta de teste" read as a placeholder. A second pass found the q8 note named only one of two uniformizações. Lighthouse: CSP blocked a `data:` font (Best Practices 92), no meta description (SEO 82), throttled LCP 3.6 s.
- Fix: divergence index on home, kind and years in list rows, Antes/Depois with per-window counts, both confidences named, chart key and readable year labels; JSON preloaded and fetched in parallel, fonts never inlined, description/canonical/Open Graph, per-route titles. Result: Best Practices 100, SEO 92, LCP 2.6 s; all 5 claims in 0–1 clicks. `robots.txt` cannot be served by a Pages project site.
- Human check: pending.

### 2026-10-15 — Site revamp: identity "duas vozes"
- Tool: Claude Code (Opus 5.5) with design skills (frontend-design, emil-design-eng, ui-ux-pro-max checklists, humanizer).
- Task: colour means a position and nothing else; mirrored year histogram; home opens with the strongest confirmed divergence; Literata and Hanken Grotesk self-hosted (ADR 0008); light and dark from one token set; plain pt-PT copy.
- Failed: base `a` styles outside a cascade layer beat Tailwind utilities; a `#conteudo` skip link would change the HashRouter route; dates rendered 29/10/2019; one busy year flattened the mini strips; every divergence was labelled "Mudança", splits included; nav links 42 px tall.
- Fix: `@layer base`; skip link moves focus; month names; square-root scale; kind-specific labels; 44 px targets. Lowest contrast 5.3:1 light, 7.9:1 dark. 21 web tests.
- Human check: pending.

### 2026-10-15 — Live check after #22; /metodo arithmetic fixed
- Tool: Claude Code (Opus 5.5).
- Task: check the deployed site after the M6–M8 merge.
- Failed: `/metodo` said "2 de 4 corretas" while the report says 2/3 (`unclear` counted in the denominator). Favicon 404 was a CDN-cached 404 from before the deploy finished.
- Fix: report's arithmetic with a regression test; favicon re-checked after the cache expired.
- Human check: owner merged #22 and confirmed the deploy.

### 2026-10-15 — M8 docs: README, NOTA.md, IA.md
- Tool: Claude Code (Opus 5.5).
- Task: rewrite the stale README; write NOTA.md (one page) and IA.md from this log; CHANGELOG by milestone.
- Failed: self-review found two unsupported statements: a judge "memory" bug that never happened, and NOTA implying the theme was chosen for its uniformização activity (found later).
- Fix: both corrected; the "byte for byte" claim re-checked.
- Human check: pending (owner reads the three documents).

### 2026-10-15 — Divergence labels: wrong rows, then AI labels disclosed
- Tool: Claude Code (Opus 5.5).
- Task: the agent asked for labels on "rows 2, 12, 17, 23" meaning column `n`; they landed on file lines, i.e. 4 hidden divergences, labelled by GitHub Copilot. The owner kept AI labels, disclosed; the agent labelled the 4 shown ones (not blind: it had read the verdicts) and added a `labeller` column.
- Failed: the instruction was ambiguous; report and `/metodo` would have attributed AI labels to a person.
- Fix: report §6 names each labeller and says it is not SPEC §9.2's human check. Shown: 2 correct, 1 incorrect, 1 unclear (2/3); hidden: 1 of 4 correct (q10 shift 2000–2005, a real divergence the judge hid).
- Human check: none of the divergence labels.

### 2026-10-15 — Label four detected divergences
- Tool: GitHub Copilot.
- Task: label rows 1, 11, 16, 22 of `data/eval/divergence_labels.csv` from the quote pair and the frozen taxonomy; `correct` only for direct opposing answers.
- Failed: none.
- Fix: q10 `correct`; q6, q8, q9 `incorrect` (q9 compares survival after judicial sale with priority over an earlier mortgage).
- Human check: owner chose the rows and the criteria; not reviewed by a jurist.

### 2026-10-15 — M6: divergence page, /metodo, a11y pass
- Tool: Claude Code (Opus 5.5).
- Task: `/divergencias/:id`, `/metodo` from `evaluation.json` (written by `make evaluate`, checked by `make data-check`), favicon; a11y checked at 360 px, light and dark.
- Failed: a stray `cat >> /dev/null` hung a run; token counts published as floats; `judge.confidence` typed as plain string.
- Fix: typed `CostOut`, narrowed type. 20 web tests, 181 pytest, data-check 0 errors.
- Human check: none.

### 2026-10-15 — Evaluation report (M7) and divergence sheet
- Tool: Claude Code (Opus 5.5).
- Task: operationalise and commit the keyword baseline (`7ed0291`) before running it; `juris/evaluate` writes `data/eval/report.md` from committed data, the local database and replay fixtures (no API calls).
- Failed: survey notes first gave a made-up rejection reason for seed 4 and missed that q5 was rejected; numbers in English format.
- Fix: reasons from `taxonomy.json`; pt-PT numbers. Test questions: model 33/42 exact vs baseline 24/42; positions recovered 20/21 vs 4/21; model positions agreeing with the label 20/28. Dev: 13/16 vs 7/16. v1 re-derived = 3 shown (equal to the live run); v2 = 4. Survey: seed 5 recovered (q10 shift 2003–2008, around the survey's 06B3805), 2 and 3 partial, 1 and 4 not evaluable. Cost ≈ 4 USD.
- Human check: none.

### 2026-10-15 — Merge conflicts and the first deploy with data (M4 done)
- Tool: Claude Code (Opus 5.5).
- Task: resolve 14 PR conflicts (main was a squash of the same tree) and verify the deployed site.
- Failed: full-page screenshot timed out; 360 px resize did not apply.
- Fix: read the rendered DOM instead; live data files equal the committed ones; phone layout left to M6.
- Human check: owner merged and confirmed the deploy.

### 2026-10-15 — Deploy gated by data-check
- Tool: Claude Code (Opus 5.5).
- Task: add a `data-check` job that the Pages build needs.
- Failed: the agent first said there was no deploy job, having grepped only `ci.yml`.
- Fix: corrected; workflow parsed (data-check → build → deploy); data-check passes locally.
- Human check: pending at the time; confirmed with the next merge.

### 2026-10-15 — Divergences documented by the STJ (AUJ cards)
- Tool: Claude Code (Opus 5.5).
- Task: curate `data/auj/auj.json` for the 3 AUJs in the subset (2014, 2019, 2021): question, conflict, each side, ruling, and the named STJ judgments, every field a verbatim quote; export, data-check and `/uniformizacoes`.
- Failed: the first 2019 "conflict" quote showed only one side; the 2014 AUJ's second side is attributed to Relação decisions, not STJ ones; a generated `\n` broke `check.py`.
- Fix: court's own statement of the opposition used; card says no STJ judgment is cited for that side. All 19 quotes grounded; 3 unit and 2 web tests. Passage selection is agent-made, not reviewed by a jurist.
- Human check: none.

### 2026-10-15 — Judge on pair rule v2; "resolved" label made factual
- Tool: Claude Code (Opus 5.5); judge claude-sonnet-5-5 (owner-run, 9 new calls, 14 reused).
- Task: v2 shows 4 split/shift, all on test questions: q7 shift 2004–2009, q8 split 2014–2024 (new pair), q9 split 2013–2021, q10 shift 2003–2008 (new); q3 dropped (both excerpts took no position). Gate G3 stays decided on v1; both reported.
- Failed: the UI called `resolved` "Uniformizada", but for q8 the AUJ (2014) precedes the shown contradiction (2019).
- Fix: label "Acórdão de uniformização no período"; export and data-check 0 errors; snapshot re-dumped.
- Human check: owner ran fetch and judge.

### 2026-10-15 — Why divergences are hidden; AUJ evidence; pair rule v2 (pre-registered)
- Tool: Claude Code (Opus 5.5).
- Task: read the 20 hidden verdicts (18 have an excerpt that takes no position; 3 truncated). Causes: the classifier positions judgments that only touch the question (8 of 28 on the labels) and v1 picks the pair by date adjacency; find the 3 AUJs in the subset; owner chose AUJ cards first, then a pre-registered pair rule.
- Failed: AUJ 4/2014 was not flagged because dgsi.pt misspells its meio processual ("JURSIPRUDÊNCIA").
- Fix: field check needs only "uniformiz" (regression test). Pair rule v2 committed to SPEC §6.2 before any v2 verdict; `quote_match` stored; v1 reproducible. `make fetch --ids-file` and `data/auj/fetch_ids.txt` for 4 cited judgments.
- Human check: pending at the time (owner's fetch and judge).

### 2026-10-15 — Judge run, Gate G3 and the committed snapshot
- Tool: Claude Code (Opus 5.5); judge claude-sonnet-5-5 (owner-run).
- Task: read 23 verdicts; record Gate G3 = STAY (q7 shift 2004–2009 and q9 split 2013–2021 confirmed on test questions). `juris/db/snapshot.py` dumps metadata, hashes, grounded quotes and verdicts (no text) and loads them into a new database; detect keeps verdicts while the evidence is unchanged.
- Failed: fresh-clone test kept 0 verdicts (evidence compared byte for byte) and counted 0 rejected quotes (NULLs ignored).
- Fix: canonical comparison and NULL-aware count. Snapshot → detect → export gives byte-identical site data.
- Human check: owner ran judge, export and data-check (0 errors with grounding).

### 2026-10-15 — Judge model rejects `temperature`
- Tool: Claude Code (Opus 5.5).
- Task: `make judge` failed: "`temperature` is deprecated for this model".
- Failed: SPEC §7 assumed temperature 0 for every call.
- Fix: `temperature=None` for the judge (unit test). Verdicts are not deterministic across live runs but stay reproducible from replay fixtures.
- Human check: owner re-ran `make judge`.

### 2026-10-15 — Full classification run and quote-grounding repairs
- Tool: Claude Code (Opus 5.5); classifier claude-haiku-4-5-20251001 (owner-run).
- Task: 813 judgments classified: 0 schema failures, ≈ 2.1 M tokens. Prompt `classify_v1` kept frozen (rule 8).
- Failed: 118 of 695 quotes (17 %) rejected for trivial differences ("...", left-out paragraph numbers, quote marks, broken hyphenation, final stop, > 400 chars), losing their positions.
- Fix: `grounding.ground` with named repairs, storing the text's own span; `--reground` from replay. A first attempt left 31 rejections; inspecting them added the spacing, "[...]" and final-stop rules. Result: 684 accepted, 11 rejected (real misquotes). Disclosed: repairs designed after inspecting rejections mostly on test questions; no repair reads the position, and position ratios barely moved (e.g. q8 17:17 → 21:18). Of 46 judge quotes, 39 exact, 5 partial.
- Human check: none at the time.

### 2026-10-15 — Optional workspace header
- Tool: Claude Code (Opus 5.5).
- Task: pilot failed: "API key is not scoped to a workspace".
- Failed: provider assumed a workspace-scoped key.
- Fix: optional `LLM_WORKSPACE_ID` sent as `anthropic-workspace-id` (unit test; `.env.example`, runbook).
- Human check: owner re-ran the pilot.

### 2026-10-15 — Show the API's error message on a failed live call
- Tool: Claude Code (Opus 5.5).
- Task: first pilot failed with a bare `400 Bad Request`.
- Failed: `raise_for_status()` dropped the response body.
- Fix: `ApiError` carries the API's error type and message (never the key); runbook lists usual causes. Unit test with a mocked 400.
- Human check: owner re-ran the pilot.

### 2026-10-15 — Evaluation labels (60 rows) filled by AI, not by a human
- Tool: Claude Code (Opus 5.5).
- Task: fill `data/eval/labels.csv` (a HUMAN task in ROADMAP M3). The owner had no time or legal training; the agent first declined, then did it on explicit instruction, from sumários only.
- Failed: methodological: labels are not human, labeller and classifier are both Claude models (agreement may be inflated), no jurist reviewed them. 29 position, 29 nao_decide, 2 unclear.
- Fix: disclosed in `data/eval/labeller.md`, the report and IA.md; still blind to the classifier (committed before any run).
- Human check: none; a jurist's review is recommended.

### 2026-10-15 — Cost guards for the live run
- Tool: Claude Code (Opus 5.5).
- Task: bound worst-case cost: 1 200-token answers, no retry of cut answers, 3 M-token budget per run, progress every 50.
- Failed: the first version retried truncated answers, paying twice.
- Fix: separate `Truncated` exception; tests for truncation and budget stop plus resume.
- Human check: none.

### 2026-10-15 — M4: export, data-check and minimal UI
- Tool: Claude Code (Opus 5.5).
- Task: `juris/export` (pydantic schemas, deterministic export, data-check in CI) and routes `/`, `/perguntas`, `/perguntas/:id`; only grounded quotes and judge-confirmed divergences published; quotes as text.
- Failed: tests rendered `<App />` without a router; an act() warning; "media" without its accent.
- Fix: `MemoryRouter`, async tests, labels in `messages.pt.ts`. 3 Python and 10 web tests; screenshot check in `vite preview`.
- Human check: none.

### 2026-10-15 — M5: judge pass and LLM runbook
- Tool: Claude Code (Opus 5.5).
- Task: `juris/detect/judge.py` (≤ 40 divergences, rule confidence, UI label, Gate G3), `make judge`/`judge-replay`, `docs/llm-runbook.md`; verdicts cached as replay fixtures.
- Failed: a generated `\n` broke an f-string; empty database printed "PIVOT"; the first version showed the judge the assigned positions, which SPEC §6.4 excludes and which would bias it.
- Fix: rewritten; gate says "not decidable" when empty; positions removed from the judge's input before any run. 8 unit tests.
- Human check: none.

### 2026-10-15 — M5: detection
- Tool: Claude Code (Opus 5.5).
- Task: pure split/shift/resolved functions, `detect.toml` with SPEC §6.2 defaults, `make detect`; written before any classification existed. Open choices fixed in SPEC §6.2 (merge overlapping splits, one shift per change, dominant also needs `k`).
- Failed: 5 of the agent's own test expectations were wrong (window spans off by a year; a "flicker" case is a real shift).
- Fix: expectations recomputed by hand; 12 synthetic tests plus a database test.
- Human check: none.

### 2026-10-15 — Gate G3 fixed before results
- Tool: Claude Code (Opus 5.5).
- Task: record the owner's pivot rule before any classification (rule 8): stay if ≥ 1 judge-confirmed divergence on a test question.
- Failed: nothing.
- Fix: n/a.
- Human check: owner chose the rule.

### 2026-10-15 — M4: classification module
- Tool: Claude Code (Opus 5.5).
- Task: provider interface, replay provider, Anthropic adapter over `httpx`; pydantic validation of the untrusted answer; classify run (sumário first, one retry on schema failure, grounding, resume, stratified pilot). The live run refuses to start until the 60 blind labels exist.
- Failed: two lines over the ruff limit; SPEC §7's signature had no place for the rendered prompt.
- Fix: wrapped; `system` added to the signature in SPEC §7. Unit tests incl. mock HTTP transport.
- Human check: none.

### 2026-10-15 — Taxonomy frozen (v1) and blind label sheet
- Tool: Claude Code (Opus 5.5).
- Task: freeze taxonomy `v1` and prompt `classify_v1`; generate the 60-row blind sheet (keyword pools, 8–9 rows per question, excluding the 195 judgments the owner had seen with an LLM answer); sheet with sumários kept local.
- Failed: SPEC §9.1 and ROADMAP T7.1 assumed 5 seed questions (only 2 approved); the discovery renderer also renders rejected questions; one test expected wrong rounding.
- Fix: SPEC/ROADMAP rewritten for the 7 approved questions before generating; approved-only renderer; ADR 0007.
- Human check: owner accepted the q6–q10 definitions, the model input and the dev split.

### 2026-10-15 — Taxonomy approved (7 questions)
- Tool: Claude Code (Sonnet 5.5).
- Task: write `data/taxonomy.json` from the owner's decision: q2, q3, q6–q10 approved; q1, q4, q5 rejected.
- Failed: q10's two found judgments sit on the same side, so it was not yet two-sided as first presented; definitions drafted from quotes, not checked by a lawyer.
- Fix: stated in q10's `seed_source`; test checks the approved ids.
- Human check: owner chose the list.

### 2026-10-14 — M3 discovery pass result (150 judgments)
- Tool: owner ran 3 packs in an LLM chat; Claude Code (Sonnet 5.5) ran `discovery.py check`.
- Task: Gate G2 and new-question proposals.
- Failed: no seed question shows a split; the tool's "10 proposed questions" was inflated by free-text labels; about 5 real two-sided questions remain. 0 quotes rejected.
- Fix: `check` prints the years behind each label; G2 criterion unchanged.
- Human check: owner approved the questions.

### 2026-10-14 — Taxonomy: allow 2–4 positions per question
- Tool: Claude Code (Sonnet 5.5).
- Task: owner asked why at most 3; relaxed to 4 (validator, SPEC §5.1, test).
- Failed: the limit was a SPEC choice, not a detection requirement.
- Fix: `2 <= positions <= 4`.
- Human check: owner decided.

### 2026-10-14 — M3 start: seed taxonomy and discovery kit
- Tool: Claude Code (Sonnet 5.5).
- Task: 5 seed questions with a pydantic validator; `discovery.py pack|check`, prompt `discovery_v0.md`, 150 random judgments in 3 packs.
- Failed: a long heredoc wrote nothing; `data/discovery/` (holds sumários) was not gitignored.
- Fix: files written with the file tool; ignore added before committing.
- Human check: owner ran the packs and approved the questions.

### 2026-10-14 — M1.5 spike result (questions 1 and 2)
- Tool: owner ran the packs in an LLM chat; Claude Code (Sonnet 5.5) ran `spike.py check`.
- Task: check quotes and positions on the full fetched pool.
- Failed: both fail the ≥ 2 positions criterion (Q1: 1 A, 19 none, its keyword filter caught other topics; Q2: 6 A, 0 B). 0 invented quotes.
- Fix: criterion unchanged; owner went on to M3 discovery.
- Human check: pending at the time (reading Q2 sumários).

### 2026-10-14 — M1.5 spike kit for questions 1 and 2
- Tool: Claude Code (Sonnet 5.5).
- Task: `spike.py -q q1|q2|q3` and prompts `spike_q1_v0.md`, `spike_q2_v0.md`; keywords fixed before any model output.
- Failed: nothing; position wording is the agent's draft.
- Fix: n/a.
- Human check: owner ran the packs.

### 2026-10-14 — Full `make fetch`: 3 processo mismatches
- Tool: Claude Code (Sonnet 5.5).
- Task: read the owner's fetch output (3 of 813 failed).
- Failed: parser bug: a nested table added "ver acórdão T REL" to the processo; the safety check caught it, nothing wrong was stored.
- Fix: `_processo_text` takes the first cell; unit test; re-run from cache with 0 requests.
- Human check: pending at the time (owner re-runs fetch and confirms 0 failures).

### 2026-10-14 — M1.5 spike result (question 3)
- Tool: owner ran the pack in an LLM chat; Claude Code (Sonnet 5.5) ran `spike.py check`.
- Task: 20 pilot sumários on "sinal e mora".
- Failed: criterion failed (9 B, 0 A, 11 none); 0 invented quotes. A forked agent correctly refused to answer the pack itself.
- Fix: none needed; criterion unchanged; next: larger pool and questions 1 and 2.
- Human check: pending at the time (spot-read 4 sumários).

### 2026-10-14 — Repo hygiene and security review
- Tool: Claude Code (Sonnet 5.5), `/security-review`.
- Task: look for env files, secrets, data, missing ignores, stale files, vulnerabilities.
- Failed: SQLite sidecar files and editor/OS files were not ignored; stale `docs/adr/.gitkeep`.
- Fix: ignores added, `.gitkeep` removed; history checked: no secrets, data or databases ever committed; no vulnerabilities found.
- Human check: owner to keep GitHub secret scanning enabled.

### 2026-10-14 — M1.5 spike kit
- Tool: Claude Code (Sonnet 5.5).
- Task: spike prompt `spike_q3_v0.md` (sinal e mora) and `pack`/`check` tool; question 3 chosen because the pilot has the most matching sumários.
- Failed: nothing.
- Fix: n/a.
- Human check: owner ran the pack.

### 2026-10-14 — Pilot completed: 91 % complete, gaps are on the site
- Tool: Claude Code (Sonnet 5.5).
- Task: inspect 9 incomplete pilot rows from the cache.
- Failed: acceptance bar (≥ 95 %) missed: 91/100; the cells are empty on dgsi.pt itself (mostly 2000–2003).
- Fix: no code change; owner chose to classify sumário-only judgments, flagged (ADR 0006).
- Human check: owner made the policy decision.

### 2026-10-14 — First live `make fetch` pilot
- Tool: Claude Code (Sonnet 5.5).
- Task: read the pilot output and the 2 incomplete rows.
- Failed: the server dropped 3 requests in a row and the run stopped (as SPEC §3 requires); the 2 rows have no full text on the site.
- Fix: nothing worked around; `--delay` can only be raised above 2.5 s.
- Human check: owner resumed later.

### 2026-10-14 — Review of the subset justification
- Tool: Claude Code (Sonnet 5.5).
- Task: explain why STJ, the descriptors, the size and 2000–2025.
- Failed: no reason for the 2000 start; seed question 1's 1998 judgment falls outside.
- Fix: owner kept 2000–2025; limitation recorded in ADR 0005 (1995–2025 would be 1 144).
- Human check: owner decided.

### 2026-10-13 — Subset decision
- Tool: Claude Code (Sonnet 5.5).
- Task: count descriptors and years in the full index, write ADR 0005, restrict `make fetch` to the subset.
- Failed: first count matched by substring (`EXTRADIÇÃO` contains `TRADIÇÃO`); fetch would have sampled all 71 760 judgments.
- Fix: whole-descriptor regex with tests; fetch restricted to the subset.
- Human check: pending at the time (skim the theme descriptors).

### 2026-10-13 — `make fetch`
- Tool: Claude Code (Sonnet 5.5).
- Task: fetch loop on the polite fetcher: stratified pilot, resume, failures listed; mock-transport tests.
- Failed: nothing.
- Fix: n/a; `ARGS` added to the Makefile target.
- Human check: owner ran the pilot.

### 2026-10-13 — `make index` and a key correction
- Tool: Claude Code (Sonnet 5.5).
- Task: index crawl loop (follow "Seguinte", resume, stop rules) with mock-transport tests.
- Failed: one case number has two judgments, so SPEC §4's `processo` key was wrong.
- Fix: keyed by `doc_id`; SPEC/ROADMAP updated; request budget corrected (≈ 740).
- Human check: pending at the time (owner to do a `--max-pages 3` live run first).

### 2026-10-13 — M1 parsers on saved fixtures
- Tool: Claude Code (Sonnet 5.5).
- Task: index, judgment and descriptor parsers from 8 saved pages; trimmed fixtures; unit and golden tests.
- Failed: `selectolax`'s default backend raises on import; the fixtures held full texts (rule 3); SPEC page-size and pagination assumptions were wrong.
- Fix: lexbor backend; `trim_fixture.py`; SPEC §3 corrected.
- Human check: pending at the time (spot-check one judgment live).

### 2026-10-13 — M1 crawler core and DB schema
- Tool: Claude Code (Sonnet 5.5).
- Task: polite fetcher (delay, cache, stop rules, host allowlist, cap) and SQLite schema.
- Failed: a long heredoc wrote nothing; `canonical_url` turned `?OpenDocument` into `?OpenDocument=`.
- Fix: file tool; raw query segments kept; regression golden file.
- Human check: pending at the time (owner to check the first live run against SPEC §3).

### 2026-10-12 — GitHub Pages deploy and README
- Tool: Claude Code (Sonnet 5.5).
- Task: deploy to GitHub Pages (SHA-pinned actions, CSP meta tag); README in pt-PT.
- Failed: `make` resolved to the npm package, and `uv` was not on PATH, so `make verify` could not run.
- Fix: documented in the README; verification left to the owner and CI.
- Human check: pending at the time (owner to run `make verify`, enable Pages, check the CI run).

### 2026-10-12 — Scope/roadmap review and edits
- Tool: Claude Code (Sonnet 5.5).
- Task: review SPEC/ROADMAP against the goal; add the feasibility spike, stratified pilot, earlier labelling, committed snapshot.
- Failed: the original brief was not available to the model.
- Fix: stated as a limitation.
- Human check: pending at the time (owner to read the SPEC/ROADMAP diff against the brief).

### 2026-10-12 — Repo scaffold
- Tool: Claude Code (Sonnet 5.5).
- Task: project structure, test layout, CI workflows, this log.
- Failed: `git clone` cannot target a non-empty folder; `uv` and `make` not installed.
- Fix: `git init` + fetch + checkout onto `origin/main`.
- Human check: pending at the time (owner to run `make setup && make verify`).
