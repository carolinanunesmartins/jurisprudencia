"""M3 T3.3 blind label sheet for position accuracy (SPEC §9.1). Offline: no network, no API key.

  make      draw 60 (judgment, question) rows from keyword candidate pools, one pool per approved
            question, and write the sheet the owner reads (data/labelling/sheet.md, gitignored:
            it contains sumários) plus the committed data/eval/labels.csv with an empty label.
  validate  check that every filled label is a position id of its question, nao_decide or unclear.

The predicates, allocation and exclusions are fixed here before any classification output exists.
Judgments already shown to the owner with an LLM answer (spike and discovery packs) are excluded,
so the labels are blind to model output. Rows are evenly spaced by date within each pool.
"""

import argparse
import csv
import json
import sqlite3
import sys
from collections.abc import Callable
from pathlib import Path

from juris.db.subset import fold
from juris.taxonomy.model import Taxonomy, load_taxonomy

SHEET = Path("data/labelling/sheet.md")
LABELS = Path("data/eval/labels.csv")
SEEN = ("data/spike/ids_*.json", "data/discovery/ids_*.json")
FIELDS = ["n", "doc_id", "processo", "data", "url", "question", "label", "notes"]
EXTRA_LABELS = ("nao_decide", "unclear")


def _has(t: str, *words: str) -> bool:
    return any(w in t for w in words)


# Candidate pools on accent-folded upper-case sumários. Noisy on purpose: nao_decide is a label.
POOLS: dict[str, Callable[[str], bool]] = {
    "q2": lambda t: "EXECUCAO ESPECIFICA" in t and _has(t, "MORA", "DEFINITIV"),
    "q3": lambda t: "SINAL" in t and _has(t, "MORA", "DEFINITIV"),
    "q6": lambda t: "PRAZO" in t and _has(t, "ABSOLUT", "RELATIV", "ESSENCIAL"),
    "q7": lambda t: "TRADICAO" in t and _has(t, "POSSE", "POSSUIDOR", "DETENTOR", "DETENCAO"),
    "q8": lambda t: "RETENCAO" in t and "CONSUMIDOR" in t,
    "q9": lambda t: "RETENCAO" in t and "HIPOTECA" in t,
    "q10": lambda t: "SINAL" in t and "EXECUCAO ESPECIFICA" in t,
}
# 60 rows: 8 per approved question, plus one more for each two-sided discovered question.
ALLOCATION = {"q2": 8, "q3": 8, "q6": 9, "q7": 9, "q8": 9, "q9": 9, "q10": 8}


def spaced(rows: list[tuple], n: int) -> list[tuple]:
    """n rows evenly spaced over rows sorted by (date, doc_id)."""
    rows = sorted(rows, key=lambda r: (r[3], r[0]))
    if len(rows) <= n:
        return rows
    step = (len(rows) - 1) / (n - 1)
    return [rows[round(i * step)] for i in range(n)]


def draw(rows: list[tuple], tax: Taxonomy, seen: set[str]) -> list[tuple[str, tuple]]:
    """(question id, row) pairs; each judgment appears once, smallest pool picks first."""
    approved = [q.id for q in tax.questions if q.status == "approved"]
    if sorted(approved) != sorted(ALLOCATION):
        raise ValueError(f"allocation {sorted(ALLOCATION)} does not match approved {approved}")
    fresh = [r for r in rows if r[4] and r[0] not in seen]
    pools = {q: [r for r in fresh if POOLS[q](fold(r[4]))] for q in approved}
    taken: set[str] = set()
    out: list[tuple[str, tuple]] = []
    for q in sorted(approved, key=lambda q: len(pools[q])):
        chosen = spaced([r for r in pools[q] if r[0] not in taken], ALLOCATION[q])
        taken |= {r[0] for r in chosen}
        out += [(q, r) for r in chosen]
    order = {q: i for i, q in enumerate(approved)}
    return sorted(out, key=lambda x: (order[x[0]], x[1][3], x[1][0]))


def _seen_ids() -> set[str]:
    ids: set[str] = set()
    for pattern in SEEN:
        for f in Path().glob(pattern):
            ids |= set(json.loads(f.read_text(encoding="utf-8")))
    return ids


def _question_block(q) -> list[str]:
    lines = [f"**{q.id} — {q.title_pt}.** {q.description_pt}", ""]
    lines += [f"- `{p.id}` ({p.label_pt}): {p.definition_pt}" for p in q.positions]
    lines += [
        "- `nao_decide`: o sumário não toma posição sobre esta pergunta.",
        "- `unclear`: não consigo decidir com segurança.",
    ]
    return lines


def make(db: Path, tax_path: Path) -> int:
    if LABELS.exists():
        print(f"{LABELS} already exists; refusing to overwrite labels", file=sys.stderr)
        return 1
    tax = load_taxonomy(tax_path)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT doc_id, processo, url, data_iso, sumario FROM acordao WHERE sumario <> ''"
    ).fetchall()
    picked = draw(rows, tax, _seen_ids())
    qs = {q.id: q for q in tax.questions}
    body = [
        f"# Folha de anotação cega (taxonomia {tax.version})",
        "",
        "Para cada linha, lê o sumário e escreve em `data/eval/labels.csv`, coluna `label`, "
        "o id da posição, `nao_decide` ou `unclear`. Usa só o sumário; o link serve para casos "
        "duvidosos. Não consultes resultados do modelo. Escreve a tua formação jurídica numa "
        "linha em `data/eval/labeller.md`.",
    ]
    current = None
    for n, (qid, (_, processo, url, data_iso, sumario)) in enumerate(picked, 1):
        if qid != current:
            body += ["", "---", "", *_question_block(qs[qid])]
            current = qid
        body += ["", f"### {n}. {qid} · Processo {processo} · {data_iso}", url, "", sumario]
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    SHEET.write_text("\n".join(body) + "\n", encoding="utf-8")
    LABELS.parent.mkdir(parents=True, exist_ok=True)
    with LABELS.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for n, (qid, (doc_id, processo, url, data_iso, _)) in enumerate(picked, 1):
            w.writerow([n, doc_id, processo, data_iso, url, qid, "", ""])
    counts = {q: sum(1 for x, _ in picked if x == q) for q in ALLOCATION}
    print(f"{len(picked)} rows {counts} -> {SHEET}, {LABELS}")
    return 0


def validate(tax_path: Path, labels: Path = LABELS) -> int:
    allowed = {
        q.id: {p.id for p in q.positions} | set(EXTRA_LABELS)
        for q in load_taxonomy(tax_path).questions
    }
    errors = filled = 0
    with labels.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            label = row["label"].strip()
            if not label:
                continue
            filled += 1
            if label not in allowed.get(row["question"], set()):
                errors += 1
                print(f"row {row['n']}: '{label}' is not valid for {row['question']}")
    print(f"{filled} labels filled, {errors} invalid")
    return 1 if errors else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    ap.add_argument("cmd", choices=["make", "validate"])
    a = ap.parse_args()
    return make(a.db, a.taxonomy) if a.cmd == "make" else validate(a.taxonomy)


if __name__ == "__main__":
    sys.exit(main())
