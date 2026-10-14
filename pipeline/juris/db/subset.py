"""The thesis subset (SPEC §2, docs/adr/0005-subset.md): contrato-promessa, 2000-2025.

Selection uses the descriptors from the index listing, so it needs no judgment text.
"""

import json
import re
import sqlite3
import unicodedata

FIRST_YEAR, LAST_YEAR = 2000, 2025

# Whole-descriptor patterns on accent-folded upper case. Substring matching is not safe:
# EXTRADICAO and CONTRADICAO contain TRADICAO, SINALAGMATICO contains SINAL.
_THEME = re.compile(r"CONTRATO[ -]+PROMESSA|^PROMESSA (DE (COMPRA|VENDA)|UNILATERAL|BILATERAL)")


def fold(text: str) -> str:
    """Upper-case and strip accents so 'Cláusula' compares equal to 'CLAUSULA'."""
    base = unicodedata.normalize("NFKD", text)
    return "".join(c for c in base if not unicodedata.combining(c)).upper()


def theme_descriptor(descriptor: str) -> bool:
    return _THEME.search(fold(descriptor)) is not None


def in_subset(data_iso: str | None, descritores: list[str]) -> bool:
    year = int((data_iso or "0000")[:4])
    return FIRST_YEAR <= year <= LAST_YEAR and any(theme_descriptor(d) for d in descritores)


def subset_ids(conn: sqlite3.Connection) -> set[str]:
    return {
        doc_id
        for doc_id, data_iso, dj in conn.execute(
            "SELECT doc_id, data_iso, descritores_json FROM acordao"
        )
        if in_subset(data_iso, json.loads(dj or "[]"))
    }
