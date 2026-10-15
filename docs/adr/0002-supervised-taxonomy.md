# ADR 0002 — Supervised taxonomy instead of unsupervised clustering

Status: accepted (2026-10-12). Recorded retroactively on 2026-10-15; the decision is in SPEC §5 and §12.

## Context
A divergence only means something when two judgments answer the same legal question in opposite ways. Clusters of similar text group topics, not answers, and their labels are not stable enough to show to a reader.

## Decision
- Questions are curated: 5 seed questions from a practitioner survey (SPEC §5.2), plus up to 3 proposed by one LLM discovery pass over a 150-judgment sample (SPEC §5.3).
- The owner approves, edits or rejects each one. Each approved question has 2–4 positions with definitions written before any judgment is classified.
- The taxonomy is frozen as `v1` (`data/taxonomy.json`, git tag `taxonomy-v1`) together with the prompt `classify_v1`.
- Embeddings and clustering stay a stretch goal and are not required.

## Consequences
- Coverage is limited to the approved questions (7 in `v1`). Anything else in the judgments is not seen.
- Each classification is a position on a defined question, so positions can be compared across years and checked against labels.
