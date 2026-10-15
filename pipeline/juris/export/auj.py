"""Divergences documented by the STJ itself (SPEC §6.6): acórdãos de uniformização (AUJ).

`data/auj/auj.json` is curated: for each AUJ in the subset, the passages where the AUJ states
the question, the conflict, each side and the ruling, and for each side the STJ judgments the
AUJ names with a passage of their own sumário. Every text field is a verbatim quote; the export
adds processo, date and dgsi.pt link from the database, and `make data-check` re-checks that
each quote is a substring of the stored text it is attributed to.
"""

import json
import sqlite3
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from juris.export.model import AujJudgmentOut, AujOut, AujSideOut

AUJ = Path("data/auj/auj.json")


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JudgmentIn(_In):
    doc_id: str
    quote: str


class SideIn(_In):
    auj_quote: str
    judgments: list[JudgmentIn]


class AujIn(_In):
    id: str
    doc_id: str
    related_questions: list[str]
    question_quote: str | None
    conflict_quote: str
    sides: list[SideIn]
    ruling_quote: str


def load_curated(path: Path = AUJ) -> list[AujIn]:
    if not path.exists():
        return []
    return [AujIn.model_validate(a) for a in json.loads(path.read_text(encoding="utf-8"))]


def doc_ids(path: Path = AUJ) -> set[str]:
    """Every judgment the AUJ cards refer to (the snapshot keeps their metadata)."""
    out = set()
    for a in load_curated(path):
        out.add(a.doc_id)
        out |= {j.doc_id for s in a.sides for j in s.judgments}
    return out


def export_aujs(conn: sqlite3.Connection, path: Path = AUJ) -> list[AujOut]:
    def meta(doc_id: str) -> tuple[str, str, str]:
        row = conn.execute(
            "SELECT processo, data_iso, url FROM acordao WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        if row is None:
            raise LookupError(f"{path}: {doc_id} is not in the database")
        return row

    out = []
    for a in load_curated(path):
        processo, date, url = meta(a.doc_id)
        sides = [
            AujSideOut(
                auj_quote=s.auj_quote,
                judgments=[
                    AujJudgmentOut(
                        doc_id=j.doc_id,
                        processo=(m := meta(j.doc_id))[0],
                        date=m[1],
                        url=m[2],
                        quote=j.quote,
                    )
                    for j in s.judgments
                ],
            )
            for s in a.sides
        ]
        out.append(
            AujOut(
                id=a.id,
                doc_id=a.doc_id,
                processo=processo,
                date=date,
                url=url,
                related_questions=a.related_questions,
                question_quote=a.question_quote,
                conflict_quote=a.conflict_quote,
                sides=sides,
                ruling_quote=a.ruling_quote,
            )
        )
    return sorted(out, key=lambda a: a.date, reverse=True)


def quotes(a: AujOut) -> list[tuple[str, str]]:
    """(doc_id, quote) for every quote on the card, for the grounding check."""
    out = [(a.doc_id, q) for q in (a.question_quote, a.conflict_quote, a.ruling_quote) if q]
    for s in a.sides:
        out.append((a.doc_id, s.auj_quote))
        out += [(j.doc_id, j.quote) for j in s.judgments]
    return out
