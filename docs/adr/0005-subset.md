# ADR 0005 — Thesis subset: contrato-promessa, STJ, 2000–2025

Status: accepted (2026-10-13). Numbers come from the full index crawl (`make index`, 723 requests) and `pipeline/tools/subset_counts.py`.

## Context
SPEC §2 fixes the rule: theme *contrato-promessa* selected by DGSI descriptors, years 2000–2025, target 600–1 500 judgments; if more, restrict to 2005–2025; if fewer than 400, widen with "Sinal" and "Execução específica".

Index facts (2026-10-13): 71 760 judgments indexed (SPEC §2 quoted 73 682 from the site's own count; 1 922 fewer were listed, not investigated, and the listing is the real universe for this project). 1932–2026, with a thin archive before 1967. Descriptor strings are free text with many spelling variants (`CONTRATO-PROMESSA`, `CONTRATO PROMESSA`, `CONTRATO - PROMESSA DE COMPRA E VENDA`, …).

## Decision
A judgment is in the subset when its date is in 2000–2025 and at least one of its descriptors names a *contrato-promessa* (regex in `pipeline/juris/db/subset.py`, matched on whole descriptors after accent folding):
- contains `CONTRATO-PROMESSA` (also with a space, or ` - `), or
- starts with `PROMESSA DE COMPRA`, `PROMESSA DE VENDA`, `PROMESSA UNILATERAL` or `PROMESSA BILATERAL`.

Result: **813 judgments** (649 if limited to 2005–2025). This is inside the 600–1 500 target, so neither the year restriction nor the widening in SPEC §2 applies. All 2000–2025 years are kept.

Per year: 2000:22, 2001:26, 2002:23, 2003:37, 2004:56, 2005:37, 2006:51, 2007:41, 2008:38, 2009:47, 2010:57, 2011:36, 2012:34, 2013:25, 2014:20, 2015:26, 2016:21, 2017:21, 2018:21, 2019:32, 2020:16, 2021:29, 2022:25, 2023:24, 2024:25, 2025:23.

`make fetch` only downloads this subset (the pilot is drawn from it, stratified by year). `--all-index` exists for exploration and is not used by the pipeline.

## Why not substring matching
A naive match on `SINAL`/`TRADIÇÃO`/`PROMESSA` catches `EXTRADIÇÃO` (267 hits), `CONTRADIÇÃO …`, `CARÁCTER SINALAGMÁTICO`, `PROMESSA DE CASAMENTO`, road-sign descriptors and similar. Whole-descriptor patterns avoid these; `test_subset.py` pins both lists.

## Consequences
- **Roughly 25–30 judgments per year**, and a dip to 16 in 2020. Time-window detection (M5) has small counts per window; thresholds in SPEC §6 must be applied as written, and per-window counts are shown in the UI.
- **Cost:** 813 fetches ≈ 40–45 minutes of polite crawling, far under the old 1–2 hour estimate.
- **Recall limits:** judgments that discuss a promessa but carry no such descriptor (or none at all) are missed. This is a stated limitation of the method, not tuned afterwards.
- **Not included:** descriptors `SINAL`, `EXECUÇÃO ESPECÍFICA`, `TRADIÇÃO DA COISA`, `CLÁUSULA PENAL` on their own (they also occur outside promessa). The SPEC §2 widening (exact `SINAL` family and `EXECUÇÃO ESPECÍFICA`) would add only 34 judgments in 2000–2025 (847 instead of 813), so it would not change the picture.
- Gate G2 (end of M3) and the M1.5 spike still decide whether this subset holds enough distinct positions.
