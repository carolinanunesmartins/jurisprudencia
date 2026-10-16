"""The TypeScript normaliser in web/src is checked against the same golden file."""

import json
from pathlib import Path

import pytest

from juris.search.normalise import normalise

pytestmark = pytest.mark.regression

GOLDEN = json.loads(
    (Path(__file__).parent / "golden" / "search_normalise.json").read_text("utf-8")
)["cases"]


@pytest.mark.parametrize("case", GOLDEN, ids=[repr(c["input"]) for c in GOLDEN])
def test_normaliser_matches_golden(case):
    assert normalise(case["input"]) == case["tokens"]
