"""`make fetch` (HUMAN-run): download judgments listed in `acordao` and parse them (ROADMAP T2.1).

Resumable: a row is pending until `fetched_at` is set, and raw pages are cached on disk, so a
re-run after a stop costs no repeated requests. The pilot is a fixed random sample stratified by
year (ROADMAP M2), chosen over *all* rows so it stays the same across runs.
All SPEC §3 rules live in `PoliteFetcher`; nothing here bypasses them.
"""

import argparse
import os
import random
import sqlite3
import sys
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import httpx

from juris.crawl.client import DEFAULT_MAX_REQUESTS, CrawlStop, FetchError, PoliteFetcher
from juris.db.schema import connect
from juris.parse.common import ParseError
from juris.parse.document import parse_document

EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_STOPPED = 0, 1, 2, 3
DEFAULT_SEED = 20261013


@dataclass
class FetchStats:
    attempted: int = 0
    stored: int = 0
    incomplete: list[str] = field(default_factory=list)  # stored, but sumário or texto empty
    failures: list[tuple[str, str]] = field(default_factory=list)  # (doc_id, reason)
    stopped: str | None = None
    finished: bool = False


def select_pilot(conn: sqlite3.Connection, size: int, seed: int = DEFAULT_SEED) -> list[str]:
    """Random sample of `size` doc_ids, proportional per year (largest remainder), deterministic."""
    by_year: dict[str, list[str]] = defaultdict(list)
    for doc_id, data_iso in conn.execute("SELECT doc_id, data_iso FROM acordao ORDER BY doc_id"):
        by_year[(data_iso or "")[:4]].append(doc_id)
    total = sum(len(v) for v in by_year.values())
    if total == 0:
        return []
    size = min(size, total)
    quotas = {y: size * len(v) / total for y, v in by_year.items()}
    take = {y: int(q) for y, q in quotas.items()}
    leftover = size - sum(take.values())
    for y in sorted(quotas, key=lambda y: (quotas[y] - take[y], y), reverse=True)[:leftover]:
        take[y] += 1
    rng = random.Random(seed)
    picked: list[str] = []
    for year in sorted(by_year):
        picked += rng.sample(by_year[year], take[year])
    return picked


def pending_ids(conn: sqlite3.Connection, candidates: list[str] | None = None) -> list[str]:
    """doc_ids not yet fetched, in a stable order (newest judgments first)."""
    rows = conn.execute(
        "SELECT doc_id FROM acordao WHERE fetched_at IS NULL ORDER BY data_iso DESC, doc_id"
    ).fetchall()
    ids = [r[0] for r in rows]
    if candidates is None:
        return ids
    wanted = set(candidates)
    return [i for i in ids if i in wanted]


def fetch_documents(
    fetcher: PoliteFetcher,
    conn: sqlite3.Connection,
    doc_ids: list[str],
    *,
    progress: Callable[[FetchStats, str], None] | None = None,
) -> FetchStats:
    """Fetch, parse and store each document. Per-document problems are listed, not fatal."""
    stats = FetchStats()
    for doc_id in doc_ids:
        url, processo = conn.execute(
            "SELECT url, processo FROM acordao WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        stats.attempted += 1
        try:
            raw = fetcher.get(url)
        except CrawlStop as stop:
            stats.attempted -= 1
            stats.stopped = str(stop)
            return stats
        except FetchError as err:
            stats.failures.append((doc_id, f"fetch: {err}"))
            continue
        try:
            doc = parse_document(raw)
        except ParseError as err:
            stats.failures.append((doc_id, f"parse: {err}"))
            continue
        if doc.processo != processo:
            stats.failures.append(
                (doc_id, f"processo mismatch: index {processo!r} vs {doc.processo!r}")
            )
            continue
        conn.execute(
            "UPDATE acordao SET secao = ?, meio_processual = ?, decisao = ?, sumario = ?,"
            " texto = ?, texto_sha256 = ?, fetched_at = ? WHERE doc_id = ?",
            (
                doc.secao,
                doc.meio_processual,
                doc.decisao,
                doc.sumario,
                doc.texto,
                doc.texto_sha256,
                datetime.now(UTC).isoformat(),
                doc_id,
            ),
        )
        conn.commit()
        stats.stored += 1
        if not doc.sumario or not doc.texto:
            stats.incomplete.append(doc_id)
        if progress:
            progress(stats, doc_id)
    stats.finished = True
    return stats


def _print_progress(stats: FetchStats, doc_id: str) -> None:
    print(f"stored {stats.stored:>5} | failures {len(stats.failures):>3} | {doc_id}", flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch dgsi.pt STJ judgments (HUMAN-run).")
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--cache", type=Path, default=Path("data/raw"))
    ap.add_argument("--max-requests", type=int, default=DEFAULT_MAX_REQUESTS)
    ap.add_argument("--pilot", type=int, default=None, help="only the stratified pilot of N")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--contact", default=os.environ.get("JURIS_CONTACT"))
    args = ap.parse_args(argv)
    if not args.contact:
        print("Set JURIS_CONTACT (or --contact): your email goes in the User-Agent (SPEC §3).")
        return EXIT_USAGE
    if not args.db.exists():
        print(f"{args.db} not found: run `make index` first.")
        return EXIT_USAGE

    conn = connect(args.db)
    candidates = select_pilot(conn, args.pilot, args.seed) if args.pilot else None
    todo = pending_ids(conn, candidates)
    print(f"{len(todo)} judgments to fetch" + (f" (pilot of {args.pilot})" if args.pilot else ""))
    with httpx.Client() as client:
        fetcher = PoliteFetcher(
            args.cache, client, contact=args.contact, max_requests=args.max_requests
        )
        stats = fetch_documents(fetcher, conn, todo, progress=_print_progress)
    print(
        f"requests {fetcher.requests_made} | stored {stats.stored}"
        f" | failures {len(stats.failures)} | empty sumário/texto {len(stats.incomplete)}"
    )
    for doc_id, reason in stats.failures:
        print(f"  FAILED {doc_id}: {reason}")
    for doc_id in stats.incomplete:
        print(f"  INCOMPLETE {doc_id}")
    if stats.stopped:
        print(f"Stopped: {stats.stopped}. Re-run later to resume (cached pages cost no requests).")
        return EXIT_STOPPED
    return EXIT_ERROR if stats.failures else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
