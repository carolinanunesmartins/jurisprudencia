# Regression tests

Golden-file tests that pin behaviour already verified by a human. Put expected outputs in
`golden/`, inputs (saved HTML, never full judgments beyond what the data policy allows) in
`../fixtures/`. Changing a golden file needs a reason in the PR description.
Planned: parser fixtures (M2), detection on synthetic matrices (M5), replay classification (M4).
