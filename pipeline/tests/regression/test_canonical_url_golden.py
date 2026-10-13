"""Regression: `?OpenDocument` was once rewritten to `?OpenDocument=` by re-encoding the query,
which would have produced duplicate cache keys and different URLs on the live site."""

import json
from pathlib import Path

import pytest

from juris.crawl.client import canonical_url

pytestmark = pytest.mark.regression

GOLDEN = json.loads((Path(__file__).parent / "golden" / "canonical_url.json").read_text("utf-8"))


@pytest.mark.parametrize("case", GOLDEN, ids=[c["id"] for c in GOLDEN])
def test_canonical_url_is_stable(case):
    assert canonical_url(case["url"]) == case["expected"]
