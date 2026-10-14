# ROADMAP.md

Status: `todo | doing | done | blocked`. Capacity assumed: **3 h per working day**, AI-assisted. Hours are [Guessing] and were under-estimated in every previous project; treat as ±40%. ★ = presentable stop point. `HUMAN:` tasks are never done by agents.

Calendar: today Mon 12/10 = day 0 (≈2 h). Days 1–9 = Tue 13/10 → Fri 23/10 (target delivery). Mon 26/10 = reserve. Weekends are optional buffer (+6 h).

## M0 — Foundation (2 h) · done · day 0
- Done 2026-10-13: scaffold merged to `main` (PR #17), CI green (`ci-ok`), live page https://carolinanunesmartins.github.io/jurisprudencia/ (HTTP 200, `lang="pt-PT"`, CSP meta).
- Owner settings confirmed done: Pages source = GitHub Actions, CI green. Secret scanning and the required `ci-ok` check: confirm in repo settings if not yet done.
- Accept: `make verify` green; CI green; empty page online. ✔

## M1 — Index crawler and subset ★ (3 h) · done · day 1 · deps: M0
Done 2026-10-13: full index run by the owner (723 requests, 71 760 judgments, `Index complete`). Subset = 813 judgments (contrato-promessa descriptors, 2000–2025), see `docs/adr/0005-subset.md`. Open: push `m1-crawler` and merge the M1 PR.
Done so far (branch `m1-crawler`): T1.1 fetcher core `pipeline/juris/crawl/client.py` (mock-transport tests); SQLite schema `pipeline/juris/db/schema.py`; HUMAN fixtures saved (3 index pages, 4 judgments, descriptor list); T1.2 parsers `pipeline/juris/parse/{index,document,descritores}.py` with unit + golden regression tests. Committed judgment fixtures are trimmed by `pipeline/tools/trim_fixture.py` (rule 3); raw saves stay in gitignored `fixtures/local_raw/`. Still to do: wire `make index` (follow "Seguinte" links, dedupe, write `acordao` rows), then HUMAN `make index` and T1.3.
Note: the saved judgments are not on the contrato-promessa theme (recent civil/penal cases); good for structure, not for the M1.5 spike.
- T1.1 Crawler per SPEC §3 (rate limit, cache, resume, stop rules) with tests against saved HTML fixtures.
- HUMAN: save 2 index pages and 3 judgment pages as fixtures (browser → save HTML) so agents can write parsers; check the real page size and encoding.
- T1.2 Index parser → `acordao` rows (doc_id, processo, relator, date, descritores, URL). Key is `doc_id`, not `processo` (SPEC §4).
- HUMAN: `make index` (≈30 min, evening). Then T1.3: list descriptors, count candidates per descriptor and year, apply SPEC §2 decision rule, write `docs/adr/0005-subset.md` with the real numbers.
- Accept: index of the whole STJ in SQLite; subset chosen with counts; ADR written.

## M1.5 — Feasibility spike (1 h) · doing · day 1–2 · deps: M1 fixtures
Result 2026-10-14, seed question 3 (sinal e mora), 20 pilot judgments spread over 2002–2025, classified from the sumário by an LLM chat pass (owner): **FAIL on the criterion** — 9 judgments position B (incumprimento definitivo required), 0 position A (mora is enough), 11 do not decide the question; 0 quotes rejected. B appears in every period (2002 to 2025), so in this sample the question looks settled, not split. One question and a keyword-selected pool of 100 fetched judgments is thin evidence; next: fetch the rest of the subset (needed anyway), rerun the spike on questions 1 and 2 (survey splits 2005 and 2008–2013) with the larger pool, before any decision to switch subset. G2 at M3 remains the real gate.
Result 2026-10-14, questions 1 and 2 on the full pool (810 fetched, 20 sumários each, same LLM-chat method, 0 quotes rejected): **both FAIL the criterion**. Q1 (execução específica vs alienação a terceiro): 1 position A, 19 nenhuma; the keyword pool was mostly off-question (precision about 1 in 20), so Q1 is untested rather than settled. Q2 (mora vs definitivo for execução específica): 6 position A (2003–2024), 0 position B; no split visible in the sumários, although the survey cites 2008–2013 judgments. Across the three seed questions only one position was ever seen per question. Pass criterion unchanged. Decision pending with the owner (see AI_LOG).
- HUMAN: take ~20 saved judgments on seed question 1 or 3 and run one LLM pass (human-run, key needed) with a draft prompt.
- Accept: at least 2 positions observed in the sample, or decide early to switch to the fallback subset (SPEC §2). Gate G2 still applies at M3 with the 150 sample, but this spike catches a bad subset before M2.

## M2 — Document crawl and parser (4 h) · todo · days 2–3 · deps: M1
- T2.1 Document fetcher (same rules), `--max-requests`. *Progress: `make fetch ARGS="--pilot 100"` implemented and tested offline (stratified pilot, resume, failures listed). Pilot done 2026-10-14 (100 stored, 0 failures after one stop on server disconnects). **Real parse rate: 91/100 with non-empty sumário and texto, below the 95% bar.** All 9 gaps are missing on the site itself (verified in the cached HTML), not parser bugs: 5 from 2000–2001 have a sumário but no full text, 2 from 2003 have full text but no sumário, 2 from 2010 have no full text. From 2004 on: 81/83 complete (97.6%). Owner decision: sumário-only judgments are classified from the sumário and flagged (ADR 0006).*
- T2.2 Parser (fixtures from M1) → `acordao.sumario/texto/decisao`; tests on ≥ 5 fixtures including footnotes and anonymised text.
- HUMAN: `make fetch` for a **pilot of 100, random and stratified by year** (not the first 100 fetched; otherwise M4 shows no time effect) (evening) and later the rest (overnight, possibly across several runs).
- Accept: `make fetch` resumes correctly after interruption (tested); ≥ 95% of fetched documents parse with non-empty sumário and texto (report the real rate); parse failures listed.

## M3 — Taxonomy ★ (3 h) · doing · days 3–4 · deps: M2 pilot
- T3.1 Seed `taxonomy.json` from SPEC §5.2. *Done 2026-10-14 (`data/taxonomy.json` + validator; q4/q5 positions are drafts for owner review).*
- T3.2 Discovery pass on 150 sampled judgments (HUMAN-run, needs key) → ≤ 3 proposed questions. *Kit ready 2026-10-14: `python pipeline/tools/discovery.py pack|check`, 3 packs of 50 in `data/discovery/`; owner pastes each into an LLM chat and saves `answer_<k>.json`.*
- HUMAN (≈45 min): approve/edit/reject questions and positions. Gate G2 (SPEC §2).
- T3.3 Freeze taxonomy + prompt version (tag it). Generate the blind label sheet for the 60-judgment position-accuracy sample now (moved from M7: it does not depend on model output).
- HUMAN (≈2 h, days 4–5): fill the 60 labels. Record the labeller's legal background in the report; single annotator is a stated limitation; allow an `unclear` label.
- Accept: `taxonomy.json` with 5–8 approved questions, each with ≥ 2 positions and definitions; taxonomy/prompt frozen before labelling.

## M4 — Vertical slice online ★ (3 h) · todo · day 4 · deps: M3
- T4.1 Classification module + `ReplayProvider` + schema + grounding check (tests with fixtures).
- HUMAN: run classification on the 100-judgment pilot; measure tokens/cost; set the API spend limit.
- T4.2 Export `web/public/data/*.json` for the pilot; minimal UI: `/perguntas` and one question timeline; deploy.
- Accept: a public URL showing real pilot data with quotes and links. If this fails, cut scope now (see Cuts).

## M5 — Full classification and detection (4 h) · todo · days 5–6 · deps: M4
- HUMAN: full `make classify` (cost limit set); keep the run log.
- T5.1 Detection per SPEC §6.2–6.5, config in `detect.toml`, unit tests on synthetic matrices (shift, split, resolved, ties, thin support).
- T5.2 Judge pass for the top divergences; store verdicts.
- T5.3 Commit `data/classifications` snapshot (metadata, position, quote, `texto_sha256`, url; no full texts) so `detect`, `export` and `data-check` run from a fresh clone.
- Day-5 checkpoint: decide cuts (judge pass, `resolved`, filters) from actual progress, not at the end.
- Accept: `divergence` table populated; every divergence has two grounded quotes and links; `make data-check` green on a fresh clone (schema, quote ≤ 400, links, fixture grounding; real-text grounding result recorded in the classify run log).

## M6 — Full UI (5 h) · todo · days 6–8 · deps: M5
- T6.1 `/`, `/perguntas`, `/perguntas/:id` (timeline, data-table alternative, filters).
- T6.2 `/divergencias/:id` side-by-side, "como foi detetado", confidence.
- T6.3 `/metodo` (filled from `data/eval/report.md` later), disclaimer, a11y pass (keyboard, focus, contrast, 360 px).
- Accept: all routes work offline-static; a11y checks have no serious issues; CSP headers applied.

## M7 — Evaluation (3 h) · todo · day 8 · deps: M5 (parallel with M6)
- T7.1 Label sheet for ≤ 30 divergences (the 60 position labels are already done in M3). Report counts alongside percentages; no confidence-interval claims at this sample size. Discovered questions beyond the 5 seeds are listed as not evaluated.
- HUMAN (≈1 h): label the divergences.
- T7.2 Metrics script and baseline; `data/eval/report.md`; survey-recovery table.
- Accept: report with measured numbers, dev/test split respected, limitations listed.

## M8 — Docs, video, submission ★ (3 h) · todo · day 9 · deps: M6, M7
- T8.1 `README.md` (pt-PT): what it is, quickstart without crawling (uses committed data), full reproduction steps, crawl policy.
- T8.2 `NOTA.md` (≤ 1 page): subset and criterion, grouping approach, divergence detection, main limitations.
- T8.3 `IA.md` from `AI_LOG.md`: tools, workflow, what worked, what failed.
- HUMAN: record a 3–4 min video (script below), submit links, optionally ask the company the three questions if still useful.
- Accept: fresh clone → `make setup && make verify` green; production URL works; all five deliverables ready.

## Video script (3–4 min)
1. Problem and subset with the criterion (20 s). 2. Questions page → one timeline (40 s). 3. A divergence card: quotes, dates, link to dgsi.pt, "como foi detetado" (60 s). 4. Method in three steps and one real limitation (40 s). 5. AI usage: what worked, what failed (40 s). 6. Evaluation numbers and next steps (20 s).

## Cuts (in this order, if behind)
1. Year/secção filters and polishing of the table alternative. 2. Judge pass (keep rules + quotes + confidence). 3. Baseline comparison. 4. Discovery pass (use only the 5 seed questions). 5. Reduce subset to ≈ 500 judgments. 6. Drop the `resolved` type. Never cut: grounding, the disclaimer, the evaluation sample of position accuracy, the live URL.

## Buffer note
Milestones sum to ≈ 31 h against 30 h of weekday capacity, and estimates have been low before. Treat weekends (+6 h) and Mon 26/10 as planned buffer, not spare. Use the day-5 checkpoint to apply cuts early.

## Calendar (3 h/day)
| Day | Date | Work |
|---|---|---|
| 0 | Mon 12/10 | M0 |
| 1 | Tue 13/10 | M1 (crawler; index run in the evening) |
| 2 | Wed 14/10 | M1 subset decision, M2 start |
| 3 | Thu 15/10 | M2 (pilot fetch/parse), M3 start |
| 4 | Fri 16/10 | M3 done, M4 vertical slice online ★ |
| 5 | Mon 19/10 | M5 (full classification running) |
| 6 | Tue 20/10 | M5 detection, M6 start |
| 7 | Wed 21/10 | M6 |
| 8 | Thu 22/10 | M6 finish, M7 |
| 9 | Fri 23/10 | M8 and submission |
| 10 | Mon 26/10 | Reserve |
