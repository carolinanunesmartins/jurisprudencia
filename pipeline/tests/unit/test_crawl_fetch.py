from pathlib import Path

import httpx
import pytest

from juris.crawl.client import PoliteFetcher
from juris.crawl.fetch import (
    EXIT_USAGE,
    fetch_documents,
    main,
    pending_ids,
    read_ids,
    select_pilot,
)
from juris.db.schema import connect

pytestmark = pytest.mark.unit

FIX = Path(__file__).parent.parent / "fixtures"
BASE = "https://www.dgsi.pt/jstj.nsf/954f0ce6ad9dd8b980256b5f003fa814/"
# (doc_id, processo, data_iso, fixture) — processo/date as in the saved judgments
DOCS = [
    ("d1", "5306/20.0T8BRG.G3.S1", "2026-10-01", "doc_1"),
    ("d2", "9454/23.6T8LSB.L1.S1", "2026-10-01", "doc_2"),
    ("d3", "586/20.3S5LSB.L1.S1", "2026-09-24", "doc_3"),
    ("d4", "23748/18.9T8LSB-A.L1.S2", "2020-11-11", "doc_2000"),
]


def url_of(doc_id: str) -> str:
    return f"{BASE}{doc_id}?OpenDocument"


class Site:
    def __init__(self, fail_on: dict[str, int] | None = None) -> None:
        self.pages = {url_of(d): (FIX / f"{f}.html").read_bytes() for d, _, _, f in DOCS}
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
    conn = connect(tmp_path / "t.db")
    for doc_id, processo, data_iso, _ in DOCS:
        conn.execute(
            "INSERT OR IGNORE INTO acordao(doc_id, processo, url, data_iso) VALUES (?,?,?,?)",
            (doc_id, processo, url_of(doc_id), data_iso),
        )
    conn.commit()
    return fetcher, conn


def test_fetch_parses_and_stores_every_pending_document(tmp_path):
    site = Site()
    fetcher, conn = make(tmp_path, site)
    stats = fetch_documents(fetcher, conn, pending_ids(conn))
    assert stats.finished and stats.stored == 4 and not stats.failures and not stats.incomplete
    row = conn.execute(
        "SELECT secao, sumario, texto, texto_sha256, fetched_at FROM acordao WHERE doc_id = 'd1'"
    ).fetchone()
    assert all(row)
    assert pending_ids(conn) == []


def test_pending_order_is_newest_first(tmp_path):
    _, conn = make(tmp_path, Site())
    assert pending_ids(conn) == ["d1", "d2", "d3", "d4"]


def test_rerun_after_stop_resumes_without_repeating_requests(tmp_path):
    site = Site(fail_on={url_of("d3"): 503})
    fetcher, conn = make(tmp_path, site)
    stats = fetch_documents(fetcher, conn, pending_ids(conn))
    assert not stats.finished and "503" in (stats.stopped or "")
    assert stats.stored == 2
    assert pending_ids(conn) == ["d3", "d4"]
    site.fail_on = {}
    fetcher2, _ = make(tmp_path, site)
    again = fetch_documents(fetcher2, conn, pending_ids(conn))
    assert again.finished and again.stored == 2
    assert site.requested.count(url_of("d1")) == 1 and site.requested.count(url_of("d2")) == 1


def test_request_cap_stops_the_run(tmp_path):
    fetcher, conn = make(tmp_path, Site(), max_requests=1)
    stats = fetch_documents(fetcher, conn, pending_ids(conn))
    assert not stats.finished and "max-requests" in (stats.stopped or "")
    assert stats.stored == 1


def test_single_http_error_is_listed_and_the_run_continues(tmp_path):
    site = Site(fail_on={url_of("d2"): 500})
    fetcher, conn = make(tmp_path, site)
    stats = fetch_documents(fetcher, conn, pending_ids(conn))
    assert stats.finished and stats.stored == 3
    assert [d for d, _ in stats.failures] == ["d2"]
    assert pending_ids(conn) == ["d2"]
    assert site.requested.count(url_of("d2")) == 1  # no retry


def test_unparseable_page_is_listed_not_stored(tmp_path):
    site = Site()
    site.pages[url_of("d1")] = b"<html><body>manutencao</body></html>"
    fetcher, conn = make(tmp_path, site)
    stats = fetch_documents(fetcher, conn, pending_ids(conn))
    assert stats.stored == 3
    assert stats.failures[0][0] == "d1" and stats.failures[0][1].startswith("parse:")
    assert "d1" in pending_ids(conn)


def test_page_for_another_processo_is_rejected(tmp_path):
    site = Site()
    site.pages[url_of("d1")] = site.pages[url_of("d2")]  # wrong judgment behind this URL
    fetcher, conn = make(tmp_path, site)
    stats = fetch_documents(fetcher, conn, pending_ids(conn))
    assert [d for d, _ in stats.failures] == ["d1"]
    assert "mismatch" in stats.failures[0][1]


def test_empty_sumario_or_texto_is_flagged_as_incomplete(tmp_path):
    site = Site()
    site.pages[url_of("d1")] = site.pages[url_of("d1")].replace(b"Sum", b"Xyz")
    fetcher, conn = make(tmp_path, site)
    stats = fetch_documents(fetcher, conn, ["d1"])
    assert stats.stored == 1 and stats.incomplete == ["d1"]


def seed_years(conn, per_year: dict[str, int]) -> None:
    for year, n in per_year.items():
        for i in range(n):
            conn.execute(
                "INSERT INTO acordao(doc_id, processo, url, data_iso) VALUES (?,?,?,?)",
                (f"{year}-{i}", f"{i}/{year}", f"u{year}{i}", f"{year}-06-01"),
            )


def test_pilot_is_stratified_by_year_and_deterministic(tmp_path):
    conn = connect(tmp_path / "t.db")
    seed_years(conn, {"2010": 100, "2015": 300, "2020": 600})
    pilot = select_pilot(conn, 100)
    assert len(pilot) == len(set(pilot)) == 100
    by_year = {y: sum(p.startswith(y) for p in pilot) for y in ("2010", "2015", "2020")}
    assert by_year == {"2010": 10, "2015": 30, "2020": 60}
    assert select_pilot(conn, 100) == pilot
    assert select_pilot(conn, 100, seed=1) != pilot


def test_pilot_draws_only_from_the_given_population(tmp_path):
    conn = connect(tmp_path / "t.db")
    seed_years(conn, {"2010": 50, "2020": 50})
    population = {f"2010-{i}" for i in range(50)}
    pilot = select_pilot(conn, 10, population=population)
    assert len(pilot) == 10 and set(pilot) <= population


def test_pilot_keeps_small_years_and_caps_at_population(tmp_path):
    conn = connect(tmp_path / "t.db")
    seed_years(conn, {"2011": 3, "2012": 3})
    assert len(select_pilot(conn, 100)) == 6
    assert select_pilot(connect(tmp_path / "empty.db"), 10) == []


def test_pilot_is_stable_once_some_documents_are_already_fetched(tmp_path):
    conn = connect(tmp_path / "t.db")
    seed_years(conn, {"2010": 50, "2020": 50})
    pilot = select_pilot(conn, 20)
    conn.execute("UPDATE acordao SET fetched_at = 'x' WHERE doc_id = ?", (pilot[0],))
    assert select_pilot(conn, 20) == pilot
    assert pilot[0] not in pending_ids(conn, pilot) and len(pending_ids(conn, pilot)) == 19


def test_main_requires_contact_and_an_existing_db(tmp_path, monkeypatch):
    monkeypatch.delenv("JURIS_CONTACT", raising=False)
    assert main(["--db", str(tmp_path / "x.db")]) == EXIT_USAGE
    assert main(["--db", str(tmp_path / "x.db"), "--contact", "a@b.c"]) == EXIT_USAGE
    assert not (tmp_path / "x.db").exists()


def test_delay_below_the_spec_minimum_is_refused(tmp_path):
    connect(tmp_path / "t.db").close()
    args = ["--db", str(tmp_path / "t.db"), "--contact", "a@b.c", "--delay", "1"]
    assert main(args) == EXIT_USAGE


def test_ids_file_lists_doc_ids_with_comments_and_no_duplicates(tmp_path):
    f = tmp_path / "ids.txt"
    f.write_text("# AUJ 2019\nd1  # fundamento\n\nd3\nd1\n", encoding="utf-8")
    assert read_ids(f) == ["d1", "d3"]


def test_ids_file_with_an_unindexed_id_is_refused_before_any_request(tmp_path):
    connect(tmp_path / "t.db").close()
    f = tmp_path / "ids.txt"
    f.write_text("nope\n", encoding="utf-8")
    args = ["--db", str(tmp_path / "t.db"), "--contact", "a@b.c", "--ids-file", str(f)]
    assert main(args) == EXIT_USAGE
