# ADR 0003 — Quote grounding as a hard gate

Status: accepted (2026-10-12; locating rules added 2026-10-15). Recorded retroactively on 2026-10-15; the decision is in SPEC §6.1 and AGENTS.md rule 4.

## Context
Every claim on the site must be checkable against the judgment. A model can paraphrase or invent a passage that reads like a quote.

## Decision
- The model must return the passage that supports its position, at most 400 characters.
- The passage is located in the stored text (`juris.classify.grounding.ground`). What is stored and shown is **the text's own span**, never the model's string.
- Locating allows only named repairs, each counted in the report: typography, a paragraph number left out, spacing or hyphens broken in the source, a missing final full stop, and "..." joins where every piece is found in order (only the longest piece is kept).
- Anything not found is rejected, stored as `quote_ok=false` and counted. Accepted fabrications must be 0.
- `make data-check` checks published quotes. CI checks grounding on fixtures only, because the full texts are never committed.

## Consequences
- In the live run, 11 of 695 answers were rejected and none was published. Their positions are lost to detection.
- The locating rules were added after the first run. They change no threshold and no prompt, and they are re-applied offline from the recorded answers (`--reground`).
