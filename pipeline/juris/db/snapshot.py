"""Committed snapshot of the classification results (ROADMAP T5.3, SPEC §11).

`dump` writes `data/classifications/*.jsonl` from the local database: judgment metadata (no
sumário, no text; `texto_sha256` identifies the text), the classifier's answers with grounded
quotes only (≤ 400 characters, the text's own words), and the divergences with the judge's
verdicts. `load` rebuilds a database from it, so `make detect`, `make export` and
`make data-check` run from a fresh clone without crawling or calling the LLM.

    python -m juris.db.snapshot dump
    python -m juris.db.snapshot load --db data/juris.db
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from juris.db.schema import connect
from juris.detect.core import uniformizacao_of
from juris.llm.prompt import CLASSIFY

SNAPSHOT = Path("data/classifications")


def _write(path: Path, rows: list[dict]) -> None:
    lines = [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows]
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8", newline="\n")


def _read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def dump(conn: sqlite3.Connection, out: Path = SNAPSHOT, prompt_version: str = CLASSIFY) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    classified = conn.execute(
        "SELECT doc_id, question_id, relevant, position_id, quote, quote_ok, quote_match,"
        " text_source, model"
        " FROM classification WHERE prompt_version = ? ORDER BY doc_id, question_id",
        (prompt_version,),
    ).fetchall()
    rows = [
        {
            "doc_id": d,
            "question_id": q,
            "relevant": bool(rel),
            "position_id": pos,
            # null = a rejected quote, withheld: it is the model's string, not the text's
            "quote": quote if ok or not quote else None,
            "quote_ok": bool(ok),
            "quote_match": match,
            "text_source": src,
            "model": model,
            "prompt_version": prompt_version,
        }
        for d, q, rel, pos, quote, ok, match, src, model in classified
    ]
    ids = sorted({r["doc_id"] for r in rows})
    acordaos = []
    for doc_id in ids:
        a = conn.execute(
            "SELECT processo, url, secao, relator, data_iso, descritores_json, meio_processual,"
            " texto_sha256, uniformizacao, texto FROM acordao WHERE doc_id = ?",
            (doc_id,),
        ).fetchone()
        proc, url, secao, relator, date, desc, meio, sha, flag, texto = a
        acordaos.append(
            {
                "doc_id": doc_id,
                "processo": proc,
                "url": url,
                "secao": secao,
                "relator": relator,
                "data_iso": date,
                "descritores": json.loads(desc or "[]"),
                "meio_processual": meio,
                "texto_sha256": sha,
                "uniformizacao": uniformizacao_of(flag, meio, texto),
            }
        )
    divergences = [
        {
            "question_id": q,
            "type": t,
            "window_start": s,
            "window_end": e,
            "evidence": json.loads(ev),
            "judge": json.loads(judge) if judge else None,
            "rule_confidence": conf,
        }
        for q, t, s, e, ev, judge, conf in conn.execute(
            "SELECT question_id, type, window_start, window_end, evidence_json, judge_json,"
            " rule_confidence FROM divergence ORDER BY question_id, type, window_start, window_end"
        )
    ]
    _write(out / "acordao.jsonl", acordaos)
    _write(out / "classification.jsonl", rows)
    _write(out / "divergence.jsonl", divergences)
    return {"acordao": len(acordaos), "classification": len(rows), "divergence": len(divergences)}


def load(db: Path, src: Path = SNAPSHOT) -> dict:
    if db.exists():
        raise FileExistsError(f"{db} exists; load builds a new database only")
    conn = connect(db)
    acordaos = _read(src / "acordao.jsonl")
    conn.executemany(
        "INSERT INTO acordao(doc_id, processo, url, secao, relator, data_iso, descritores_json,"
        " meio_processual, texto_sha256, uniformizacao) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                a["doc_id"],
                a["processo"],
                a["url"],
                a["secao"],
                a["relator"],
                a["data_iso"],
                json.dumps(a["descritores"], ensure_ascii=False),
                a["meio_processual"],
                a["texto_sha256"],
                int(a["uniformizacao"]),
            )
            for a in acordaos
        ],
    )
    rows = _read(src / "classification.jsonl")
    conn.executemany(
        "INSERT INTO classification(doc_id, question_id, relevant, position_id, quote, quote_ok,"
        " quote_match, text_source, model, prompt_version) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [
            (
                r["doc_id"],
                r["question_id"],
                int(r["relevant"]),
                r["position_id"],
                r["quote"],
                int(r["quote_ok"]),
                r.get("quote_match"),
                r["text_source"],
                r["model"],
                r["prompt_version"],
            )
            for r in rows
        ],
    )
    divergences = _read(src / "divergence.jsonl")
    conn.executemany(
        "INSERT INTO divergence(question_id, type, window_start, window_end, evidence_json,"
        " judge_json, rule_confidence) VALUES (?,?,?,?,?,?,?)",
        [
            (
                d["question_id"],
                d["type"],
                d["window_start"],
                d["window_end"],
                json.dumps(d["evidence"]),
                json.dumps(d["judge"], ensure_ascii=False) if d["judge"] else None,
                d["rule_confidence"],
            )
            for d in divergences
        ],
    )
    conn.commit()
    conn.close()
    return {"acordao": len(acordaos), "classification": len(rows), "divergence": len(divergences)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("action", choices=["dump", "load"])
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--dir", type=Path, default=SNAPSHOT)
    a = ap.parse_args()
    if a.action == "dump":
        print(dump(connect(a.db), a.dir))
        return 0
    try:
        print(load(a.db, a.dir))
    except FileExistsError as e:
        print(e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
