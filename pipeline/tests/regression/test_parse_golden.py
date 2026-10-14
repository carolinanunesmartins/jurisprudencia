"""Regression: parser output on the committed (trimmed) fixtures is pinned to golden files.
Regenerate with `python pipeline/tests/regression/test_parse_golden.py --update` only after
checking the diff by hand against the page; explain the change in the PR."""

import sys
from pathlib import Path

import pytest

from juris.parse.document import parse_document

pytestmark = pytest.mark.regression

HERE = Path(__file__).parent
FIX = HERE.parent / "fixtures"
GOLDEN = HERE / "golden"
DOCS = ["doc_1", "doc_2", "doc_3", "doc_2000"]


@pytest.mark.parametrize("name", DOCS)
def test_document_parse_matches_golden(name):
    got = parse_document((FIX / f"{name}.html").read_bytes()).summary_json()
    assert got == (GOLDEN / f"{name}.parsed.json").read_text("utf-8")


if __name__ == "__main__" and "--update" in sys.argv:
    for n in DOCS:
        out = parse_document((FIX / f"{n}.html").read_bytes()).summary_json()
        (GOLDEN / f"{n}.parsed.json").write_text(out, encoding="utf-8", newline="\n")
        print("updated", n)
