"""`make detect`: classification -> divergence table (SPEC §6.2). Local and deterministic.

Only grounded positions count (relevant=1, quote_ok=1) from the current prompt version and
approved questions. Rule confidence (§6.5) needs the judge verdict and is filled in T5.2.
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from juris.db.schema import connect
from juris.detect.core import Point, detect, load_config, uniformizacao_of
from juris.llm.prompt import CLASSIFY
from juris.taxonomy.model import load_taxonomy

DEV = ("q2", "q3")  # SPEC §9.7


def points_by_question(conn: sqlite3.Connection, prompt_version: str = CLASSIFY):
    rows = conn.execute(
        "SELECT c.question_id, a.doc_id, a.data_iso, c.position_id, c.quote, a.url,"
        " a.uniformizacao, a.meio_processual, a.texto"
        " FROM classification c JOIN acordao a USING (doc_id)"
        " WHERE c.relevant = 1 AND c.quote_ok = 1 AND c.prompt_version = ?"
        " ORDER BY a.data_iso, a.doc_id",
        (prompt_version,),
    )
    out: dict[str, list[Point]] = {}
    for qid, doc_id, date, pos, quote, url, flag, meio, texto in rows:
        uni = uniformizacao_of(flag, meio, texto)
        out.setdefault(qid, []).append(Point(doc_id, date, pos, quote, url, uni))
    return out


def _canonical(evidence: dict) -> str:
    return json.dumps(evidence, sort_keys=True, ensure_ascii=False)


def run(conn: sqlite3.Connection, tax_path: Path, cfg_path: Path) -> list:
    cfg = load_config(cfg_path)
    approved = [q.id for q in load_taxonomy(tax_path).questions if q.status == "approved"]
    points = points_by_question(conn)
    found = []
    # a verdict stays with a divergence whose evidence (the pair the judge saw) did not change,
    # so re-running detect after the judge does not lose the verdicts
    kept = {
        (q, t, s, e, _canonical(json.loads(ev))): (judge, conf)
        for q, t, s, e, ev, judge, conf in conn.execute(
            "SELECT question_id, type, window_start, window_end, evidence_json, judge_json,"
            " rule_confidence FROM divergence WHERE judge_json IS NOT NULL"
        )
    }
    conn.execute("DELETE FROM divergence")
    for qid in approved:
        pts = points.get(qid, [])
        divs = detect(qid, pts, cfg)
        found += divs
        rows = []
        for d in divs:
            ev = d.evidence()
            key = (d.question_id, d.type, d.window_start, d.window_end, _canonical(ev))
            rows.append((*key[:4], json.dumps(ev), *kept.get(key, (None, None))))
        conn.executemany(
            "INSERT INTO divergence(question_id, type, window_start, window_end, evidence_json,"
            " judge_json, rule_confidence) VALUES (?,?,?,?,?,?,?)",
            rows,
        )
        split = "dev" if qid in DEV else "test"
        support = dict(sorted(Counter(p.position for p in pts).items()))
        types = dict(Counter(d.type for d in divs))
        print(f"{qid} [{split}] positioned: {support or 'none'}; divergences: {types or 'none'}")
    conn.commit()
    test = [d for d in found if d.question_id not in DEV and d.type in ("split", "shift")]
    print(f"\n{len(found)} divergences; {len(test)} split/shift on test questions go to the judge")
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    ap.add_argument("--config", type=Path, default=Path("detect.toml"))
    a = ap.parse_args()
    run(connect(a.db), a.taxonomy, a.config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
