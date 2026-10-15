# AGENTS.md — jurisprudencia

Read order for any agent: this file → `SPEC.md` → `ROADMAP.md` (take the first milestone with status `todo` whose dependencies are `done`).
Language: code, docs for agents and commit messages in English. User-facing text (UI, README, NOTA.md, IA.md) in pt-PT.

## 1. What this is
A prototype that aggregates Portuguese Supreme Court (STJ) judgments by legal question and shows **where and when the case law diverged or changed**. Data source: dgsi.pt. Output: a static web app plus a reproducible Python pipeline. It is a hiring-test submission: speed to a working, verifiable result matters more than breadth. Every claim shown to a user must carry a verbatim quote and a link to the original judgment.

## 2. Commands (must exist after M0; keep names stable)
| Command | Purpose |
|---|---|
| `make setup` | `uv sync` + `npm --prefix web ci` |
| `make verify` | ruff + pytest unit & regression (offline, fixtures only) + web typecheck/lint/test/build. **Must pass before every commit** |
| `make index` / `make fetch` | **HUMAN-run only**: crawl dgsi.pt (see SPEC §3) |
| `make classify` | **HUMAN-run only**: calls the LLM API on the full subset (needs `LLM_API_KEY`) |
| `make classify-replay` | offline run against recorded fixtures (agents may run this) |
| `make detect` / `make export` | local, deterministic, from the SQLite database |
| `make data-check` | validates `web/public/data/*.json` against schemas and the quote-grounding rule |
| `make web-dev` | Vite dev server |

## 3. Layout
```
pipeline/juris/{crawl,parse,db,llm,taxonomy,classify,detect,export,evaluate}/
pipeline/tests/{fixtures,unit,regression}/   unit = isolated logic; regression = golden files in regression/golden/
data/                    committed: taxonomy.json, eval/labels.csv, eval/report.md
data/raw/ data/*.db      gitignored (HTML cache, full texts)
web/                     Vite + React + TS + Tailwind; reads web/public/data/*.json
docs/{adr/,arquitetura.md,llm-runbook.md}
AGENTS.md SPEC.md ROADMAP.md README.md NOTA.md IA.md AI_LOG.md CHANGELOG.md LICENSE
```

## 4. Hard rules (violating any = reject the change)
1. **Agents never contact dgsi.pt.** Crawling is HUMAN-run (`make index`, `make fetch`). Agents work from HTML fixtures saved in `pipeline/tests/fixtures/`.
2. Crawler behaviour is fixed by SPEC §3 (single connection, ≥2.5 s delay, cache, stop on 429/503). Do not add concurrency, retries on rejection, header spoofing, or ways around blocks.
3. **Never commit full judgment texts** or the HTML cache. Committed data = metadata, model labels, and quotes ≤ 400 characters with a link.
4. **Quote grounding is a hard gate**: any quote shown must be a verbatim substring (after whitespace normalisation) of the stored text. The stored quote is the text's own span, located as in SPEC §6.1, never the model's copy. Accepted fabrications must be 0; rejected ones are counted and reported.
5. LLM output is untrusted: validate with pydantic, never execute or render it as HTML.
6. Agents never see or request `LLM_API_KEY`. Live LLM calls are HUMAN-run. Agents use the replay provider (SPEC §7).
7. No legal-advice claims anywhere. The UI states "sinal para revisão, não é parecer jurídico".
8. No thresholds invented after seeing results: defaults are in SPEC §6; tuning happens only on the dev split; report on the test split.
9. Minimal dependencies; a new runtime dependency needs a line in `docs/adr/`.
10. User-facing strings only in `web/src/messages.pt.ts`.
11. **`AI_LOG.md` must be kept up to date.** Any change made with AI assistance (agent or human using an AI tool) adds an entry in the same PR: tool, task, what failed, how it was fixed, what a human verified. A PR without it is rejected. `IA.md` is derived from this file.

## 5. Definition of Done (per PR)
- `make verify` green; new logic has unit tests; parsers have fixture tests.
- Acceptance checklist of the milestone in `ROADMAP.md` ticked in the PR description.
- `AI_LOG.md` has an entry for the work (tool, task, what failed, how it was fixed) — see rule 11.
- Bug fixes add a regression case (`pipeline/tests/regression/golden/` or `web/tests/regression/`).
- No `any`, no `# type: ignore` / `// @ts-ignore` without a reason comment, no skipped tests.

## 6. Autonomous workflow
- Branch `m<N>-<slug>`, Conventional Commits, one PR per milestone, squash merge by the owner after CI is green.
- Uncertain or irreversible (data policy, cost, scope)? Use the default in SPEC §12. If none, write `BLOCKERS.md` (what, options, recommended default), open a draft PR and stop.
- Tasks tagged `HUMAN:` in ROADMAP are never attempted by agents; list them in the PR description.
