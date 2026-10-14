from pathlib import Path

import httpx
import pytest

from juris.crawl.client import FetchError, PoliteFetcher
from juris.crawl.index import EXIT_USAGE, START_URL, crawl_index, main
from juris.db.acordao import insert_index_rows
from juris.db.schema import connect
from juris.parse.common import ParseError
from juris.parse.index import IndexRow

pytestmark = pytest.mark.unit

FIX = Path(__file__).parent.parent / "fixtures"
P2_URL = "https://www.dgsi.pt/jstj.nsf?OpenDatabase&Start=132"
P3_URL = "https://www.dgsi.pt/jstj.nsf?OpenDatabase&Start=235"


def last_page() -> bytes:
    # index_2000 stands in for the final page: its 'Seguinte' link is removed
    return (FIX / "index_2000.html").read_bytes().replace(b"Seguinte", b"Fim")


def live_like(raw: bytes) -> bytes:
    """The live site serves root-relative hrefs; browser-saved fixtures have them absolute."""
    return raw.replace(b"https://www.dgsi.pt", b"")


class Site:
    """Three chained pages: p1 -> p2 (Start=132) -> last (Start=235)."""

    def __init__(self, fail_on: dict[str, int] | None = None) -> None:
        self.pages = {
            START_URL: live_like((FIX / "index_p1.html").read_bytes()),
            P2_URL: live_like((FIX / "index_p2.html").read_bytes()),
            P3_URL: live_like(last_page()),
        }
        self.fail_on = fail_on or {}
        self.requested: list[str] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        self.requested.append(url)
        if url in self.fail_on:
            return httpx.Response(self.fail_on[url])
        return httpx.Response(200, content=self.pages[url])


def make(tmp_path, site, **kw):
    client = httpx.Client(transport=httpx.MockTransport(site))
    fetcher = PoliteFetcher(
        tmp_path / "raw", client, contact="x@example.com", sleep=lambda _s: None, **kw
    )
    return fetcher, connect(tmp_path / "t.db")


def test_walks_all_pages_dedupes_overlap_and_finishes(tmp_path):
    site = Site()
    fetcher, conn = make(tmp_path, site)
    stats = crawl_index(fetcher, conn)
    assert stats.finished and stats.stopped is None
    assert stats.pages == 3
    assert site.requested == [START_URL, P2_URL, P3_URL]
    assert stats.rows == 99 + 100 + 100
    assert stats.duplicates == 1  # last row of p1 repeats as first row of p2
    assert stats.inserted == 298
    assert conn.execute("SELECT COUNT(*) FROM acordao").fetchone()[0] == 298


def test_rows_are_stored_with_iso_dates_and_json_descriptors(tmp_path):
    fetcher, conn = make(tmp_path, Site())
    crawl_index(fetcher, conn)
    row = conn.execute(
        "SELECT url, relator, data_iso, descritores_json FROM acordao WHERE processo = ?",
        ("5306/20.0T8BRG.G3.S1",),
    ).fetchone()
    assert row[0].endswith("?OpenDocument") and row[1] == "CATARINA SERRA"
    assert row[2] == "2026-10-01" and row[3].startswith('["DIVORCIO SEM CONSENTIMENTO"')


def test_rerun_resumes_from_cache_with_no_requests(tmp_path):
    site = Site()
    fetcher, conn = make(tmp_path, site)
    crawl_index(fetcher, conn)
    n = len(site.requested)
    fetcher2, _ = make(tmp_path, site)
    stats = crawl_index(fetcher2, conn)
    assert len(site.requested) == n
    assert stats.finished and stats.inserted == 0


def test_stop_on_503_keeps_earlier_pages_and_reports_it(tmp_path):
    site = Site(fail_on={P2_URL: 503})
    fetcher, conn = make(tmp_path, site)
    stats = crawl_index(fetcher, conn)
    assert not stats.finished and "503" in (stats.stopped or "")
    assert stats.pages == 1
    assert conn.execute("SELECT COUNT(*) FROM acordao").fetchone()[0] == 99
    # resuming later: page 1 is cached, only the failed URL is requested again
    site.fail_on = {}
    fetcher2, _ = make(tmp_path, site)
    again = crawl_index(fetcher2, conn)
    assert again.finished
    assert site.requested.count(START_URL) == 1


def test_request_cap_stops_the_walk(tmp_path):
    fetcher, conn = make(tmp_path, Site(), max_requests=2)
    stats = crawl_index(fetcher, conn)
    assert not stats.finished and "max-requests" in (stats.stopped or "")
    assert stats.pages == 2


def test_max_pages_option(tmp_path):
    fetcher, conn = make(tmp_path, Site())
    stats = crawl_index(fetcher, conn, max_pages=1)
    assert stats.pages == 1 and not stats.finished


def test_link_back_to_a_visited_page_ends_the_walk(tmp_path):
    site = Site()
    site.pages[P3_URL] = (
        (FIX / "index_2000.html")
        .read_bytes()
        .replace(
            b"https://www.dgsi.pt/jstj.nsf?OpenDatabase&amp;Start=13299",
            P2_URL.replace("&", "&amp;").encode(),
        )
    )
    fetcher, conn = make(tmp_path, site)
    stats = crawl_index(fetcher, conn)
    assert stats.finished and stats.pages == 3


def test_non_index_page_raises_instead_of_looping(tmp_path):
    site = Site()
    site.pages[START_URL] = b"<html><body>login required</body></html>"
    fetcher, conn = make(tmp_path, site)
    with pytest.raises(ParseError):
        crawl_index(fetcher, conn)


def test_single_http_error_raises_fetch_error_without_retry(tmp_path):
    site = Site(fail_on={START_URL: 500})
    fetcher, conn = make(tmp_path, site)
    with pytest.raises(FetchError):
        crawl_index(fetcher, conn)
    assert site.requested == [START_URL]


def test_same_processo_with_different_documents_keeps_both(tmp_path):
    """Real case on the saved pages: 1748/25.2T8OAZ.P1.S1, judgments of 2026-07-13 and 09-15."""
    conn = connect(tmp_path / "t.db")
    base = "https://www.dgsi.pt/jstj.nsf/954f0ce6ad9dd8b980256b5f003fa814/"
    a = IndexRow("1/20.0T8LSB.L1.S1", base + "a1?OpenDocument", "2020-01-01", "X", ("D",))
    b = IndexRow("1/20.0T8LSB.L1.S1", base + "b2?OpenDocument", "2021-01-01", "X", ("D",))
    s = insert_index_rows(conn, [a, b, b])
    assert (s.inserted, s.duplicates) == (2, 1)
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM acordao WHERE processo = '1/20.0T8LSB.L1.S1'"
        ).fetchone()[0]
        == 2
    )


def test_real_fixture_contains_a_processo_with_two_documents(tmp_path):
    fetcher, conn = make(tmp_path, Site())
    crawl_index(fetcher, conn)
    n = conn.execute(
        "SELECT COUNT(*) FROM acordao WHERE processo = '1748/25.2T8OAZ.P1.S1'"
    ).fetchone()[0]
    assert n == 2


def test_main_requires_a_contact_and_does_no_network(tmp_path, monkeypatch):
    monkeypatch.delenv("JURIS_CONTACT", raising=False)
    assert main(["--db", str(tmp_path / "x.db")]) == EXIT_USAGE
