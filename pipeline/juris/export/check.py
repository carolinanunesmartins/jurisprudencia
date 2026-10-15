"""`make data-check`: validate web/public/data/*.json (SPEC §11, AGENTS.md rules 3-4).

Always: schemas, quotes <= 400 characters, dgsi.pt links, cross-references. When the local
database is present: every published quote is a verbatim substring of the stored text it came
from (CI has no database and checks grounding on fixtures in the unit tests).
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from juris.classify.grounding import is_grounded
from juris.export.auj import quotes
from juris.export.model import AujOut, DivergenceOut, JudgmentOut, Meta, QuestionOut

DATA = Path("web/public/data")
SOURCE = "https://www.dgsi.pt/"


def check(data: Path = DATA, db: Path | None = None) -> list[str]:
    errors: list[str] = []

    def load(name: str, adapter: TypeAdapter):
        path = data / name
        if not path.exists():
            errors.append(f"{name}: missing")
            return None
        try:
            return adapter.validate_json(path.read_text(encoding="utf-8"))
        except ValidationError as e:
            errors.append(f"{name}: {e}")
            return None

    meta = load("meta.json", TypeAdapter(Meta))
    questions = load("questions.json", TypeAdapter(list[QuestionOut])) or []
    judgments = load("judgments.json", TypeAdapter(list[JudgmentOut])) or []
    divergences = load("divergences.json", TypeAdapter(list[DivergenceOut])) or []
    aujs = load("aujs.json", TypeAdapter(list[AujOut])) or []
    if meta is None:
        return errors
    positions = {q.id: {p.id for p in q.positions} for q in questions}
    docs = {j.doc_id for j in judgments}
    for j in judgments:
        if j.position not in positions.get(j.question_id, set()):
            errors.append(f"judgment {j.doc_id}: unknown {j.question_id}/{j.position}")
        if not j.url.startswith(SOURCE):
            errors.append(f"judgment {j.doc_id}: link is not to dgsi.pt")
    for d in divergences:
        if d.question_id not in positions:
            errors.append(f"divergence {d.id}: unknown question")
        for p in d.pair:
            if p.doc_id not in docs:
                errors.append(f"divergence {d.id}: {p.doc_id} not among published judgments")
    for a in aujs:
        for q in a.related_questions:
            if q not in positions:
                errors.append(f"auj {a.id}: unknown question {q}")
        links = [a.url] + [j.url for s in a.sides for j in s.judgments]
        if not all(u.startswith(SOURCE) for u in links):
            errors.append(f"auj {a.id}: link is not to dgsi.pt")
        if len(a.sides) < 2:
            errors.append(f"auj {a.id}: needs two sides")
    if meta.divergences_shown != len(divergences):
        errors.append("meta.divergences_shown does not match divergences.json")
    if db is not None and db.exists():
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        for j in judgments:
            row = conn.execute(
                "SELECT sumario, texto FROM acordao WHERE doc_id = ?", (j.doc_id,)
            ).fetchone()
            text = "" if row is None else (row[0] if j.text_source == "sumario" else row[1])
            if not is_grounded(j.quote, text or ""):
                errors.append(f"judgment {j.doc_id}/{j.question_id}: quote not grounded")
        for a in aujs:
            for doc_id, quote in quotes(a):
                row = conn.execute(
                    "SELECT sumario, texto FROM acordao WHERE doc_id = ?", (doc_id,)
                ).fetchone()
                text = "" if row is None else "\n".join(t or "" for t in row)
                if not is_grounded(quote, text):
                    errors.append(f"auj {a.id}: quote not grounded in {doc_id}: {quote[:40]}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=DATA)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    a = ap.parse_args()
    errors = check(a.data, a.db)
    grounding = "with grounding" if a.db.exists() else "no database: grounding skipped"
    for e in errors:
        print(e)
    print(f"data-check ({grounding}): {len(errors)} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
