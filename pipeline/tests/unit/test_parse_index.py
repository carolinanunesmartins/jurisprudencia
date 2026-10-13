from pathlib import Path

import pytest

from juris.parse.common import ParseError, us_date_to_iso
from juris.parse.index import parse_index

pytestmark = pytest.mark.unit

FIX = Path(__file__).parent.parent / "fixtures"
BASE = "https://www.dgsi.pt/jstj.nsf?OpenDatabase"


def load(name):
    return parse_index((FIX / name).read_bytes(), BASE)


def test_first_page_rows_and_fields():
    page = load("index_p1.html")
    assert len(page.rows) == 99
    first = page.rows[0]
    assert first.processo == "5306/20.0T8BRG.G3.S1"
    assert first.sessao_iso == "2026-10-01"
    assert first.relator == "CATARINA SERRA"
    assert first.descritores[:2] == ("DIVORCIO SEM CONSENTIMENTO", "ATO PROCESSUAL")
    assert first.url.startswith("https://www.dgsi.pt/jstj.nsf/954f0ce6ad9dd8b980256b5f003fa814/")
    assert first.url.endswith("?OpenDocument")


def test_next_link_is_followed_not_computed():
    assert load("index_p1.html").next_url == "https://www.dgsi.pt/jstj.nsf?OpenDatabase&Start=132"
    assert load("index_p2.html").next_url == "https://www.dgsi.pt/jstj.nsf?OpenDatabase&Start=235"


def test_consecutive_pages_overlap_by_one_row():
    p1, p2 = load("index_p1.html"), load("index_p2.html")
    assert p1.rows[-1].processo == p2.rows[0].processo


def test_deep_page_has_older_dates_and_few_descriptors():
    page = load("index_2000.html")
    assert page.rows[0].sessao_iso == "2020-11-11"
    assert page.rows[0].descritores == ("REVISTA EXCECIONAL", "RELEVÂNCIA JURÍDICA")


def test_all_row_urls_are_unique_canonical_document_urls():
    rows = load("index_p2.html").rows
    assert len({r.url for r in rows}) == len(rows)
    assert all("Highlight" not in r.url and r.url.endswith("?OpenDocument") for r in rows)


def test_doc_id_is_the_url_document_segment_and_unique_per_page():
    rows = load("index_p2.html").rows
    assert rows[0].doc_id == "20d11c14734e9a1680258e80004f6fb7"
    assert len({r.doc_id for r in rows}) == len(rows)


def test_same_processo_can_have_two_documents_on_one_page():
    rows = [r for r in load("index_p2.html").rows if r.processo == "1748/25.2T8OAZ.P1.S1"]
    assert len(rows) == 2 and rows[0].doc_id != rows[1].doc_id


def test_us_date_conversion_and_rejection():
    assert us_date_to_iso("09/24/2026") == "2026-09-24"
    with pytest.raises(ParseError):
        us_date_to_iso("24/09/2026")


def test_page_without_rows_is_a_parse_error():
    with pytest.raises(ParseError):
        parse_index(b"<html><body>nothing</body></html>", BASE)


def test_root_relative_links_as_served_live_are_resolved_against_the_page_url():
    """Live regression: hrefs are '/jstj.nsf?...' (no host); a browser-saved copy hides this."""
    raw = (FIX / "index_p1.html").read_bytes().replace(b"https://www.dgsi.pt", b"")
    page = parse_index(raw, BASE)
    assert page.next_url == "https://www.dgsi.pt/jstj.nsf?OpenDatabase&Start=132"
    assert page.rows[0].url.startswith("https://www.dgsi.pt/jstj.nsf/954f0ce6")
    assert page.rows[0].doc_id == "d2523b00ca3b3d3e80258e88003cc00d"
