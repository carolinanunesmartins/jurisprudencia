"""Regression: pins grounding verdicts for previously verified cases.
Add a case to golden/grounding.json whenever a bug is fixed or a new edge is found."""

import json
from pathlib import Path

import pytest

from juris.classify.grounding import is_grounded

pytestmark = pytest.mark.regression

GOLDEN = json.loads((Path(__file__).parent / "golden" / "grounding.json").read_text("utf-8"))


@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_grounding_verdict_is_stable(case):
    assert is_grounded(case["quote"], case["text"]) is case["expected"]
