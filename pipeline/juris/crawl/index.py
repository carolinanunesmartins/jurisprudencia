"""`make index` (HUMAN-run): walk the 'Por Ano' listing and fill `acordao` (ROADMAP T1.2/T1.3).

Follows the 'Seguinte' links (never computes `Start`), stores each page's rows as it goes, and
relies on the on-disk cache for resuming: pages already fetched are re-read for free, so simply
run it again after a stop. Rules of SPEC §3 live in `PoliteFetcher`; nothing here bypasses them.
"""

import argparse
import os
import sqlite3
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx

from juris.crawl.client import (
    DEFAULT_MAX_REQUESTS,
    CrawlStop,
    FetchError,
    PoliteFetcher,
    canonical_url,
)
from juris.db.acordao import insert_index_rows
from juris.db.schema import connect
from juris.parse.common import ParseError
from juris.parse.index import parse_index

START_URL = "https://www.dgsi.pt/jstj.nsf?OpenDatabase"
EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_STOPPED = 0, 1, 2, 3


@dataclass
class IndexStats:
    pages: int = 0
    rows: int = 0
    inserted: int = 0
    duplicates: int = 0
    oldest_iso: str | None = None
    stopped: str | None = None
    finished: bool = False


def crawl_index(
    fetcher: PoliteFetcher,
    conn: sqlite3.Connection,
    *,
    start_url: str = START_URL,
    max_pages: int | None = None,
    progress: Callable[[IndexStats, int], None] | None = None,
) -> IndexStats:
    """Walk the listing from `start_url`. Returns when the list ends or a stop rule fires.

    Raises FetchError/ParseError: after those the next link is unknown, so the run must end.
    """
    stats = IndexStats()
    seen: set[str] = set()
    url: str | None = start_url
    while url:
        key = canonical_url(url)
        if key in seen:  # a link back to a visited page also means the end of the list
            break
        if max_pages is not None and stats.pages >= max_pages:
            stats.stopped = f"max-pages reached ({max_pages})"
            return stats
        seen.add(key)
        try:
            raw = fetcher.get(url)
        except CrawlStop as stop:
            stats.stopped = str(stop)
            return stats
        page = parse_index(raw)
        result = insert_index_rows(conn, page.rows)
        conn.commit()
        stats.pages += 1
        stats.rows += len(page.rows)
        stats.inserted += result.inserted
        stats.duplicates += result.duplicates
        stats.oldest_iso = min(r.sessao_iso for r in page.rows)
        if progress:
            progress(stats, len(page.rows))
        url = page.next_url
    stats.finished = True
    return stats


def _print_progress(stats: IndexStats, page_rows: int) -> None:
    print(
        f"page {stats.pages:>4} | +{page_rows:>3} rows | total new {stats.inserted:>6}"
        f" | oldest {stats.oldest_iso}",
        flush=True,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Crawl the dgsi.pt STJ index (HUMAN-run).")
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--cache", type=Path, default=Path("data/raw"))
    ap.add_argument("--max-requests", type=int, default=DEFAULT_MAX_REQUESTS)
    ap.add_argument("--max-pages", type=int, default=None)
    ap.add_argument("--contact", default=os.environ.get("JURIS_CONTACT"))
    args = ap.parse_args(argv)
    if not args.contact:
        print("Set JURIS_CONTACT (or --contact): your email goes in the User-Agent (SPEC §3).")
        return EXIT_USAGE

    args.db.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(args.db)
    with httpx.Client() as client:
        fetcher = PoliteFetcher(
            args.cache, client, contact=args.contact, max_requests=args.max_requests
        )
        try:
            stats = crawl_index(fetcher, conn, max_pages=args.max_pages, progress=_print_progress)
        except (FetchError, ParseError) as err:
            print(f"ERROR, run ended (re-run to resume from the cache): {err}")
            return EXIT_ERROR
    total = conn.execute("SELECT COUNT(*) FROM acordao").fetchone()[0]
    print(
        f"requests {fetcher.requests_made} | pages {stats.pages} | new {stats.inserted}"
        f" | duplicates {stats.duplicates} | db total {total}"
    )
    if stats.finished:
        print("Index complete.")
        return EXIT_OK
    print(f"Stopped: {stats.stopped}. Re-run later to resume (cached pages cost no requests).")
    return EXIT_STOPPED


if __name__ == "__main__":
    sys.exit(main())
