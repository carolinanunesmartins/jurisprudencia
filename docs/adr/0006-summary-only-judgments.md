# ADR 0006 — Judgments without full text are classified from the sumário, and flagged

Status: accepted (2026-10-14, owner decision).

## Context
The first live pilot (100 judgments drawn from the subset, stratified by year) parsed 91/100 with both a sumário and a full text, below the ROADMAP M2 bar of 95%. All 9 gaps are empty on dgsi.pt itself (verified in the cached HTML): 7 judgments have a sumário but an empty "Decisão Texto Integral" (five from 2000–2001, two from 2010) and 2 from 2003 have full text but no sumário. From 2004 on, 81/83 were complete. The sample of early years is tiny (6 judgments in 2000–2001), so the rate for those years is a signal, not an estimate.

## Decision
- A judgment with a full text is classified from the full text, as in SPEC §6.1.
- A judgment with a sumário but **no full text** is classified from the sumário alone. Quote grounding is unchanged: the quote must be a verbatim substring (after whitespace normalisation) of the stored sumário, and the ≤ 400 character limit applies.
- A judgment with neither is excluded and counted in the report.
- The stored source is recorded per classification (`text_source` = `texto` | `sumario`, added in M4) and the UI marks the sumário-only ones ("só sumário") on the judgment list and on the divergence card.
- Detection (SPEC §6.2) counts them like any other classified judgment. The report states how many classified judgments are sumário-only, per question and per window, and the evaluation sample of 60 includes at least a few of them so their accuracy is measured separately.

## Alternatives considered
- Exclude them: simplest and strictest, but 2000–2001 would be nearly empty and the timeline would start in about 2002 without saying so.
- Exclude and start the window in 2002: honest, but loses data the court did publish.

## Consequences
- A sumário is written by the court and is shorter and more conclusory than the reasoning, so a position read from it may be less reliable. This is measured, not assumed (see above) and stated in `/metodo`.
- The quote shown for a sumário-only judgment is from the sumário, which the UI says.
- AGENTS.md rule 4 ("stored text") is read as: `sumario` or `texto`, whichever the classification used.
- Revisit if the sumário-only accuracy on the labelled sample is clearly worse than for full texts: then exclude them.
