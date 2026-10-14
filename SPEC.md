# SPEC.md — jurisprudencia

Normative. MUST/SHOULD per RFC 2119. Confidence tags: [Certain] verified in research, [Likely] strong inference, [Guessing] to validate in the first milestone that touches it.

## 1. Goal and non-goals
**Goal.** Given a bounded set of STJ judgments from dgsi.pt, (a) group them by legal **question**, (b) assign each judgment a **position** on each question it decides, (c) detect and show **shifts, splits and resolutions** over time, with verbatim evidence.
**Non-goals.** Free-text search engine (dgsl.pt, jurisprudencia.pt and dejure.pt already do breadth), chat/RAG, accounts, multiple courts, full DGSI coverage, legal advice, model training.

## 2. Subset (decision and criteria)
- **Court:** Supremo Tribunal de Justiça (`jstj.nsf`, 73 682 documents [Certain]).
- **Theme:** *contrato-promessa* (sinal, incumprimento, execução específica, tradição, cláusula penal), selected by DGSI **descritores** (exact strings taken from the court's descriptor list in M1) intersected with years **2000–2025**.
- **Result (M1, ADR 0005):** the full index lists 71 760 judgments; the rule below gives **813** (descriptor regex in `pipeline/juris/db/subset.py`), so no restriction or widening was needed.
- **Size target:** 600–1 500 judgments. If the filter yields more, restrict years to 2005–2025; if fewer than 400, widen descriptors to include "Sinal" and "Execução específica" explicitly.
- **Why:** (1) one court, one document format, curated descriptors and summaries; (2) apex court, so divergences matter; (3) a published practitioner survey identifies concrete STJ splits on this theme (§5.2), which gives a head start and an independent check; (4) civil/contractual text, low in sensitive personal data; (5) volume fits a polite crawl of ~1–2 hours.
- **Early spike (M1.5):** before the full crawl, a ~20-judgment LLM pass must show ≥ 2 positions on one seed question; otherwise switch subset early.
- **Pilot sample:** the 100-judgment pilot is random, stratified by year.
- **Gate G2 (end of M3):** if the 150-judgment sample shows fewer than 3 questions with ≥ 2 observed positions each, pivot to the fallback subset (STJ, arrendamento urbano) before building anything else.

## 3. Responsible crawling (REQ-CRAWL)
- Source robots.txt: none present (checked by the owner on 2026-10-12). Absence of robots.txt is not permission: the rules below apply regardless.
- One connection, one request at a time. Delay between requests ≥ 2.5 s plus 0–1 s jitter. Timeout 30 s.
- `User-Agent: jurisprudencia-prototype/0.1 (contact: <owner email>)`.
- Cache every response on disk (`data/raw/`), keyed by canonical URL; never request a URL twice. Resume after interruption.
- Stop the run at the first HTTP 429/503 or after 3 consecutive errors. No retry loops, no workarounds. Resume manually later.
- Per-run cap `--max-requests` (default 800). Run off-peak (evening/night).
- Canonical URL form for documents: `https://www.dgsi.pt/jstj.nsf/<view-id>/<doc-id>?OpenDocument` (no `Highlight=`).
- Index pages [Certain, verified on saved pages 2026-10-13]: the "Por Ano" listing `https://www.dgsi.pt/jstj.nsf?OpenDatabase`, about 100 rows per page, sorted by date descending. Pagination: follow the page's "Seguinte" link. `Start=<n>` values are Domino view positions (1, 132, 235, … 13299), not multiples of the page size, so they MUST NOT be computed. The last row of a page repeats as the first row of the next: de-duplicate by `doc_id`, never by `processo`. Columns: sessão, processo (link), relator, descritor (one per line); dates mm/dd/yyyy.
- Document pages [Certain]: key/value table; fields Processo, Nº Convencional (secção), Relator, Descritores, Data do Acordão, Votação, Texto Integral, Privacidade, Meio Processual, Decisão, Indicações Eventuais (optional), Sumário, Decisão Texto Integral. Footnotes are inline; some links carry `file:///` residues.
- Descriptor list: `https://www.dgsi.pt/jstj.nsf/desc?OpenPage` (4 477 entries on the saved copy; dual spellings written "A / B *").
- Budget: the index is ≈ 740 requests (73 682 judgments at ≈ 100 rows per page, +1 overlap row per page) ≈ 40 min at ≈ 3 s each, within the default cap of 800; plus 600–1 500 documents ≈ 1.3–2.5 h in total [Likely]. Runs stop at the cap; re-running resumes from the cache.
- Encoding: windows-1252 (meta charset on all saved pages) [Certain]; decode with cp1252.

## 4. Data model (SQLite, `data/juris.db`, gitignored)
- `acordao(doc_id PK, processo, url, secao, relator, data_iso, descritores_json, meio_processual, decisao, sumario, texto, texto_sha256, fetched_at)`
- `classification(doc_id, question_id, relevant, position_id NULL, quote, quote_ok, model, prompt_version, created_at, PK(doc_id, question_id))`
- `doc_id` is the 32-hex document id in the URL (`.../<view-id>/<doc_id>?OpenDocument`). `processo` is NOT unique: one case number can have several judgments (e.g. `1748/25.2T8OAZ.P1.S1`: 2026-07-13 and 2026-09-15, found on the saved index pages 2026-10-13), so it is an indexed column only.
- `divergence(id PK, question_id, type, window_start, window_end, evidence_json, judge_json, rule_confidence)`
Parsing rules: header table → key/value; "Sumário" and "Decisão Texto Integral" sections; footnotes kept; strip `file:///` residues and spacer images; normalise whitespace; keep text local only.

## 5. Taxonomy
### 5.1 Structure (`data/taxonomy.json`)
`questions[{id, title_pt, description_pt, norms[], positions[{id, label_pt, definition_pt}], seed_source, status}]`. 2–3 mutually exclusive positions per question plus the implicit `nao_decide`.
### 5.2 Seed questions (from a practitioner survey of STJ case law on incumprimento do contrato-promessa; to be verified against the judgments themselves) 
1. Execução específica quando o promitente-vendedor alienou a terceiro antes do registo da acção (eficácia real da promessa). Reference points named in the survey: acórdão uniformizador of 05/11/1998 (proc. 086931) vs STJ 05/05/2005 (proc. 05B743).
2. Pressuposto da execução específica: mora vs incumprimento definitivo (survey cites STJ 04/03/2008, 19/05/2010, 09/12/2010 and 26/09/2013, proc. 564/11.3TVLSB.L1.S1).
3. Sinal e mora (art. 442.º, n.º 2 CC): basta a mora ou exige-se incumprimento definitivo (survey: STJ 2006–2012).
4. Redução equitativa da cláusula penal aplicada ao sinal (art. 812.º CC) (survey: STJ 18/11/2004 vs earlier decisions 1977, 1983).
5. Presunção de afastamento da execução específica quando há sinal (art. 830.º, n.º 2 CC) e tradição da coisa (survey: STJ 19/12/2006, proc. 06B3805; TRP 20/01/2005).
Source caveat [Likely]: one survey article (author and exact date not confirmed), covering decisions up to about 2013. Later shifts may exist and some positions may have moved.
### 5.3 Discovery
M3 runs one LLM pass over a random sample of 150 judgments to propose up to 3 further questions; the owner approves, edits or rejects each. Final target: 5–8 questions. Status values: `seed | proposed | approved | rejected`.

## 6. Classification and detection
### 6.1 Per-judgment classification (REQ-CLS)
Judgments with no full text are classified from the sumário alone and flagged `text_source=sumario` (ADR 0006); those with neither are excluded and counted.
One call per judgment, all approved questions at once. Input: header fields, sumário, and the reasoning sections truncated to ≈ 6 000 tokens. Output (pydantic): for each question `{relevant: bool, position_id | null, quote, note}`. `quote` ≤ 400 chars, verbatim. Rejected if not a substring (after whitespace normalisation) → stored as `relevant=false` with `quote_ok=false` and counted.
Temperature 0, one retry on schema failure only, prompts versioned in `pipeline/juris/llm/prompts/*.md`.
### 6.2 Detection (REQ-DET), pure functions over `classification`
Definitions use calendar-year windows and are configurable (`detect.toml`). Defaults, fixed before looking at results:
- **window** 3 years, sliding by 1; **min support** `k = 2` judgments per position in a window; **dominance** = position with ≥ 60% of the window's positioned judgments.
- **split:** in a window, ≥ 2 positions each reach `k`.
- **shift:** the dominant position of window W₂ differs from that of an earlier window W₁ (both with support ≥ `k`), with W₂ starting after W₁ ends.
- **resolved:** a judgment flagged as uniformização (meio processual or text marker, §6.3) falls inside or after a split/shift on the same question.
- Each divergence stores the strongest opposing pair (latest of the earlier dominant position vs earliest of the later one) with quotes and links.
### 6.3 Uniformização marker
Flag when `meio_processual` or the first 2 000 characters of the text contain "uniformização de jurisprudência" (case-insensitive, accent-insensitive). Heuristic; precision reported in the evaluation.
### 6.4 Judge pass (REQ-JUDGE)
For the ≤ 40 strongest divergences: a larger model receives only the two quotes, dates and the question and returns `{real_opposition, legislative_change_possible, rationale, confidence}`. A divergence is shown as **"mudança de entendimento"** only if `real_opposition` and not `legislative_change_possible`; if `legislative_change_possible`, it is shown as **"possível efeito de alteração legislativa"**; otherwise hidden but counted in the report.
### 6.5 Rule confidence
`alta` = support ≥ 3 on both sides and judge agrees; `média` = support ≥ 2 and judge agrees; `baixa` = otherwise. Displayed next to every divergence.

## 7. LLM access
- Provider interface `LlmProvider.generate_json(prompt_id, input) -> dict`. First adapter: Anthropic (env `LLM_API_KEY`, models from `CLASSIFY_MODEL`, `JUDGE_MODEL`).
- `ReplayProvider`: fixtures keyed by sha256 of the canonical request JSON, used in tests and `make classify-replay`.
- Cost control: measure tokens on the 100-judgment pilot, extrapolate, and set a spend limit on the API key before the full run (HUMAN). Prefer prompt caching of the taxonomy and instructions, and the provider's batch endpoint if it fits.

## 8. Web app (REQ-UI)
Static site: Vite + React + TypeScript (strict) + Tailwind; custom SVG timeline with d3-scale; HashRouter; data from `web/public/data/*.json`. Hosting: GitHub Pages (decided 2026-10-12), deployed by GitHub Actions.
Routes:
- `/` summary: subset, counts, method in one paragraph, disclaimer.
- `/perguntas` question cards: question, #judgments, years, divergence badges (mudança / divisão / uniformizada).
- `/perguntas/:id` timeline (x = year, lanes = positions, dots = judgments, marker = uniformização), filter by year/secção, list of judgments, divergence cards.
- `/divergencias/:id` before/after side by side: position, date, relator, secção, quote, link to dgsi.pt, "como foi detetado" panel (rules, judge verdict, confidence).
- `/metodo` method, limits, evaluation numbers, AI usage.
Quality bar: keyboard navigable, visible focus, colour-blind-safe palette with non-colour encodings, a data-table alternative for the chart, responsive from 360 px, `lang="pt-PT"`. No analytics, no third-party requests.
CSP via `<meta http-equiv>` in `web/index.html` (GitHub Pages cannot set headers; `frame-ancestors` is therefore not enforceable): `default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; connect-src 'self'`.

## 9. Evaluation (REQ-EVAL), outputs in `data/eval/report.md`
1. **Position accuracy:** owner labels 60 judgments (stratified: 12 per seed question) blind to model output → accuracy and confusion matrix vs the model.
2. **Divergence precision:** owner labels up to 30 detected divergences as correct / incorrect / legislative-change / unclear → precision per type.
3. **Survey recovery:** for each of the five seed questions, does the system find the split or shift the survey describes? Table of yes/partial/no with evidence.
4. **Baseline:** keyword heuristic (opposing decision words within the same descriptor) on the same labelled set.
5. **Grounding:** quotes proposed, accepted, rejected (hard gate: accepted fabrications = 0).
6. **Cost and time:** tokens, currency, minutes per stage.
7. **Split:** two questions are the dev set (tune `detect.toml` here); the rest are the test set. Report test results only for the test set; report dev separately.
No target numbers are invented in advance; report what is measured.

## 10. Security and privacy
- Judgments are published by the State and partly anonymised; the pipeline must not attempt re-identification and must not add personal data.
- Committed artefacts: metadata, labels, quotes ≤ 400 characters, links. Full texts and the HTML cache stay local.
- Secrets only via environment variables; `.env` is gitignored; secret scanning enabled on the repo.
- Static site, no cookies, no analytics.

## 11. Repo and CI (REQ-REPO)
- CI (GitHub Actions, SHA-pinned actions, `permissions: contents: read`): ruff, pytest, web typecheck/lint/test/build, `make data-check` (schema + fixture grounding), deploy job to GitHub Pages.
- Conventional Commits; `CHANGELOG.md`; short ADRs for: static site, supervised taxonomy instead of unsupervised clustering, quote grounding, polite-crawl policy, hosting.
- Reproducibility: `data/classifications` (metadata, labels, quotes, `texto_sha256`, url) is committed so `detect`, `export` and `data-check` work from a fresh clone. Grounding against real text happens at classify time and its result is logged; CI checks grounding on fixtures only.
- Skip: Docker, Husky, i18n, mutation testing, release automation.

## 12. Decisions and defaults
| Item | Default |
|---|---|
| Repo | `carolinanunesmartins/jurisprudencia` (exists; 1 commit, README only) |
| Licence | MIT for code; derived data CC BY 4.0 with link to source; judgments remain from dgsi.pt |
| Published excerpts | quotes ≤ 400 chars + links; no full texts, no full summaries |
| LLM | Anthropic; small model for classification, larger model for taxonomy discovery and the judge |
| Grouping method | supervised taxonomy (curated by descriptor + approved questions), with LLM-assisted discovery on a sample; embeddings/clustering is a stretch goal and not required |
| Hosting | GitHub Pages (decided 2026-10-12) |
| Data licence | Verify dgsi.pt's reuse notice before claiming CC BY 4.0; record in an ADR |
| Language | UI/README/NOTA/IA in pt-PT; code and agent docs in English |
| Fallback subset | STJ, arrendamento urbano |
