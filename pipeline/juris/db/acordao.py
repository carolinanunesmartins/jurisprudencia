"""Writes for the `acordao` table from index rows (the full text is filled later, in M2)."""

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass

from juris.parse.index import IndexRow


@dataclass
class InsertStats:
    inserted: int = 0
    duplicates: int = 0  # same doc_id already stored (e.g. the row repeated across pages)


def insert_index_rows(conn: sqlite3.Connection, rows: Iterable[IndexRow]) -> InsertStats:
    stats = InsertStats()
    for row in rows:
        cur = conn.execute(
            "INSERT OR IGNORE INTO acordao"
            "(doc_id, processo, url, relator, data_iso, descritores_json)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                row.doc_id,
                row.processo,
                row.url,
                row.relator,
                row.sessao_iso,
                json.dumps(list(row.descritores), ensure_ascii=False),
            ),
        )
        if cur.rowcount:
            stats.inserted += 1
        else:
            stats.duplicates += 1
    return stats
