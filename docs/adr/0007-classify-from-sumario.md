# ADR 0007 — Classify from the sumário first; the full text is the fallback

Status: accepted (2026-10-15, owner decision). Amends ADR 0006 and SPEC §6.1.

## Context
Position accuracy (SPEC §9.1) compares the model with 60 owner labels. The owner cannot read 60 full STJ judgments in the ≈ 2 h budget, so the labels are read from the sumário. If the model read the full text, disagreements would partly measure "sumário vs full text" rather than model error. The spike and the discovery pass (M1.5, M3) were also run on sumários, with every quote grounded.

## Decision
- A judgment with a sumário is classified from the header fields and the **sumário** (`text_source=sumario`).
- A judgment without a sumário but with a full text is classified from the full text, truncated as in SPEC §6.1 (`text_source=texto`). At the M2 fetch that is 13 of 813.
- A judgment with neither is excluded and counted, as before.
- Quote grounding is against whichever text was used.

## Alternatives considered
- Full text first (ADR 0006 as written): may find positions the sumário omits, but the evaluation would no longer measure the model alone, and it costs about 10× the input tokens.

## Consequences
- Positions stated only in the reasoning are missed; the report states this limitation.
- The label sample cannot include the 13 text-only judgments (no sumário to label from), so their accuracy is not measured.
- The UI marker "só sumário" from ADR 0006 is replaced by a marker on the few text-only judgments.
- Revisit if the owner's spot checks show sumários often omit the position the judgment takes.
