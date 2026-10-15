"""`make export`: SQLite -> web/public/data/*.json. Local and deterministic (no timestamps).

Publishes metadata, grounded quotes (<= 400 characters) and links only (AGENTS.md rule 3).
A split/shift is published only if the judge confirmed it (SPEC §6.4); the rest are counts.
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from juris.db.schema import connect
from juris.db.subset import subset_ids
from juris.detect.__main__ import DEV
from juris.detect.core import uniformizacao_of
from juris.detect.judge import Verdict, display
from juris.export.model import (
    DivergenceOut,
    JudgeOut,
    JudgmentOut,
    Meta,
    PairItem,
    PositionOut,
    QuestionOut,
)
from juris.llm.prompt import CLASSIFY
from juris.taxonomy.model import load_taxonomy

OUT = Path("web/public/data")


def _judgments(conn: sqlite3.Connection, approved: list[str]) -> list[JudgmentOut]:
    rows = conn.execute(
        "SELECT a.doc_id, a.processo, a.data_iso, a.url, a.secao, a.relator, c.question_id,"
        " c.position_id, c.quote, c.text_source, a.uniformizacao, a.meio_processual, a.texto"
        " FROM classification c JOIN acordao a USING (doc_id)"
        " WHERE c.relevant = 1 AND c.quote_ok = 1 AND c.prompt_version = ?"
        " ORDER BY c.question_id, a.data_iso, a.doc_id",
        (CLASSIFY,),
    )
    out = []
    for doc_id, proc, date, url, secao, relator, qid, pos, quote, src, flag, meio, texto in rows:
        if qid not in approved:
            continue
        out.append(
            JudgmentOut(
                doc_id=doc_id,
                processo=proc,
                date=date,
                url=url,
                secao=secao or "",
                relator=relator or "",
                question_id=qid,
                position=pos,
                quote=quote,
                text_source=src or "sumario",
                uniformizacao=uniformizacao_of(flag, meio, texto),
            )
        )
    return out


def _divergences(
    conn: sqlite3.Connection, approved: list[str], by_doc: dict[str, JudgmentOut]
) -> tuple[list[DivergenceOut], Counter[str]]:
    counts: Counter[str] = Counter()
    shown: list[DivergenceOut] = []
    shown_keys: set[tuple[str, str, int, int]] = set()
    rows = conn.execute(
        "SELECT question_id, type, window_start, window_end, evidence_json, judge_json,"
        " rule_confidence FROM divergence ORDER BY question_id, type DESC, window_start"
    ).fetchall()  # type DESC: split/shift before resolved, so resolved can check what is shown
    for qid, kind, start, end, ev_json, judge_json, conf in rows:
        if qid not in approved:
            continue
        ev = json.loads(ev_json)
        verdict = Verdict.model_validate_json(judge_json) if judge_json else None
        if kind == "resolved":
            target = ev.get("resolves")
            if not target or (qid, target[0], target[1], target[2]) not in shown_keys:
                continue
            label = "uniformizada"
        else:
            if verdict is None:
                counts["unjudged"] += 1
                continue
            label = display(verdict)
            if label is None:
                counts["hidden"] += 1
                continue
            shown_keys.add((qid, kind, start, end))
        pair = [
            PairItem(
                doc_id=p["doc_id"],
                processo=by_doc[p["doc_id"]].processo if p["doc_id"] in by_doc else "",
                date=p["date"],
                url=p["url"],
                position=p["position"],
                quote=p["quote"],
            )
            for p in ev["pair"]
        ]
        shown.append(
            DivergenceOut(
                id=f"{qid}-{kind}-{start}-{end}",
                question_id=qid,
                type=kind,
                window_start=start,
                window_end=end,
                display=label,
                rule_confidence=conf,
                support=ev["support"],
                pair=pair,
                judge=JudgeOut(**verdict.model_dump()) if verdict else None,
            )
        )
    counts["shown"] = len(shown)
    return shown, counts


def export(conn: sqlite3.Connection, tax_path: Path, out: Path = OUT) -> Meta:
    tax = load_taxonomy(tax_path)
    approved = [q.id for q in tax.questions if q.status == "approved"]
    judgments = _judgments(conn, approved)
    by_doc = {j.doc_id: j for j in judgments}
    divergences, dcounts = _divergences(conn, approved, by_doc)
    questions = []
    for q in tax.questions:
        if q.status != "approved":
            continue
        mine = [j for j in judgments if j.question_id == q.id]
        years = [int(j.date[:4]) for j in mine]
        questions.append(
            QuestionOut(
                id=q.id,
                title=q.title_pt,
                description=q.description_pt,
                split="dev" if q.id in DEV else "test",
                positions=[
                    PositionOut(id=p.id, label=p.label_pt, definition=p.definition_pt)
                    for p in q.positions
                ],
                counts=dict(sorted(Counter(j.position for j in mine).items())),
                first_year=min(years) if years else None,
                last_year=max(years) if years else None,
            )
        )
    classified = conn.execute(
        "SELECT text_source, COUNT(DISTINCT doc_id) FROM classification"
        " WHERE prompt_version = ? GROUP BY text_source ORDER BY text_source",
        (CLASSIFY,),
    ).fetchall()
    (rejected,) = conn.execute(
        "SELECT COUNT(*) FROM classification WHERE prompt_version = ? AND quote_ok = 0"
        " AND (quote IS NULL OR quote <> '')",  # NULL: rejected, withheld in the snapshot
        (CLASSIFY,),
    ).fetchone()
    meta = Meta(
        taxonomy_version=tax.version,
        prompt_version=CLASSIFY,
        subset_size=len(subset_ids(conn)),
        classified=sum(n for _, n in classified),
        by_source={src or "sumario": n for src, n in classified},
        quotes_rejected=rejected,
        divergences_shown=dcounts["shown"],
        divergences_hidden=dcounts["hidden"],
        divergences_unjudged=dcounts["unjudged"],
    )
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "meta.json": meta.model_dump(),
        "questions.json": [q.model_dump() for q in questions],
        "judgments.json": [j.model_dump() for j in judgments],
        "divergences.json": [d.model_dump() for d in divergences],
    }
    for name, data in files.items():
        text = json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        (out / name).write_text(text, encoding="utf-8")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    meta = export(connect(a.db), a.taxonomy, a.out)
    print(meta.model_dump_json(indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
