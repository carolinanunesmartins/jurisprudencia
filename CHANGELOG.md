# Changelog

All notable changes. Format: Conventional Commits, newest first. Details per step in AI_LOG.md.

## Unreleased
- docs: `docs/arquitetura.md`, architecture of the MVP and of its continuation (Mermaid diagrams, four phases), highlighted in the README
- chore: housekeeping; ADRs 0001–0004 (required by SPEC §11, recorded retroactively); README and AI_LOG condensed; `DgsiLink` renders only dgsi.pt links (security hardening)
- feat(web): minimal reading (emphasis by position colour, badges, details behind a click); brief verifiable in 0–1 clicks; faster load and SEO (M9)
- feat(web): visual identity "duas vozes", mirrored year chart, self-hosted type (ADR 0008) (M9)
- fix(web): `/metodo` divergence review uses the report's arithmetic
- docs: README, NOTA.md and IA.md for submission (M8)
- feat(web): `/divergencias/:id`, `/metodo` from `evaluation.json`, favicon, a11y pass (M6)
- feat(evaluate): `make evaluate` report with pre-registered keyword baseline, v1/v2 divergences, survey recovery; divergence labels by AI, disclosed (M7)
- feat(auj): divergences documented by the STJ itself (`/uniformizacoes`), every text a verified quote
- feat(detect): pair rule v2 (pre-registered); uniformização marker survives the dgsi.pt typo; verdicts kept across re-detection
- feat(data): committed snapshot `data/classifications/`, fresh clone reproduces the site data (T5.3)
- feat(classify): grounding locates quotes with named repairs and stores the text's own span; `--reground`; cost guards
- feat: classification of 813 judgments, detection, judge, Gate G3 = stay on contrato-promessa (M4, M5)
- feat: taxonomy v1 (7 questions), blind label sheet, discovery and spike kits (M1.5, M3)
- feat(crawl): polite index and document crawler, parsers, subset of 813 (M1, M2)
- chore: initial scaffold (pipeline, web, tests, CI, Pages deploy) (M0)
