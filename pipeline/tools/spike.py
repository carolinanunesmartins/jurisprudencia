"""M1.5 feasibility spike helpers (ROADMAP M1.5). Offline: no network, no API key.

  pack   pick ~20 fetched judgments for a seed question (q1, q2 or q3, SPEC §5.2) and write a
         prompt file the owner pastes into any LLM chat (HUMAN-run).
  check  read the model's JSON answer, verify every quote against the stored sumário
         (AGENTS.md rule 4) and print the positions found per year.

Everything lands in data/spike/ (gitignored: it contains sumários). Files are per question:
pack_<q>.md and ids_<q>.json. Candidate keywords are fixed here, before any model output.
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from juris.classify.grounding import is_grounded
from juris.db.subset import fold

PROMPTS = Path(__file__).parent.parent / "juris" / "llm" / "prompts"
OUT = Path("data/spike")
POSITIONS = ("A", "B")


def _q1(t: str) -> bool:
    return "EXECUCAO ESPECIFICA" in t and ("ALIEN" in t or "EFICACIA REAL" in t or "TERCEIRO" in t)


def _q2(t: str) -> bool:
    return "EXECUCAO ESPECIFICA" in t and ("MORA" in t or "DEFINITIV" in t)


def _q3(t: str) -> bool:
    return "SINAL" in t and ("MORA" in t or "DEFINITIV" in t)


QUESTIONS = {"q1": _q1, "q2": _q2, "q3": _q3}


def is_candidate(sumario: str, q: str = "q3") -> bool:
    return QUESTIONS[q](fold(sumario))


def pick(
    rows: list[tuple[str, str, str, str]], n: int, q: str = "q3"
) -> list[tuple[str, str, str, str]]:
    """Evenly spaced by date over the candidates, so the sample spans the whole period."""
    cands = sorted((r for r in rows if r[3] and is_candidate(r[3], q)), key=lambda r: (r[2], r[0]))
    if len(cands) <= n:
        return cands
    step = (len(cands) - 1) / (n - 1)
    return [cands[round(i * step)] for i in range(n)]


def pack(db: Path, n: int, q: str = "q3") -> int:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT doc_id, processo, data_iso, sumario FROM acordao WHERE fetched_at IS NOT NULL"
    ).fetchall()
    chosen = pick(rows, n, q)
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [(PROMPTS / f"spike_{q}_v0.md").read_text(encoding="utf-8")]
    for i, (_, processo, data_iso, sumario) in enumerate(chosen, 1):
        parts.append(f"\n### Acórdão {i}\nProcesso {processo} · {data_iso}\n\n{sumario}\n")
    (OUT / f"pack_{q}.md").write_text("\n".join(parts), encoding="utf-8")
    (OUT / f"ids_{q}.json").write_text(json.dumps([r[0] for r in chosen]), encoding="utf-8")
    print(f"{len(chosen)} judgments ({len(rows)} fetched) -> {OUT / f'pack_{q}.md'}")
    print("years:", ", ".join(r[2][:4] for r in chosen))
    return 0


def check(db: Path, answer: Path, q: str = "q3") -> int:
    ids = json.loads((OUT / f"ids_{q}.json").read_text(encoding="utf-8"))
    text = answer.read_text(encoding="utf-8").strip()
    if text.startswith("```"):  # tolerate a fenced block around the JSON
        text = text.strip("`").removeprefix("json").strip()
    items = json.loads(text)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    seen: Counter[str] = Counter()
    grounded: Counter[str] = Counter()
    rejected = 0
    print(f"{'n':>2} {'year':>4} {'pos':>8} grounded")
    for item in items:
        doc_id = ids[item["n"] - 1]
        data_iso, sumario = conn.execute(
            "SELECT data_iso, sumario FROM acordao WHERE doc_id = ?", (doc_id,)
        ).fetchone()
        pos = item.get("posicao", "nenhuma")
        ok = is_grounded(item.get("citacao", ""), sumario or "")
        if pos in POSITIONS:
            seen[pos] += 1
            if ok:
                grounded[pos] += 1
            else:
                rejected += 1
        mark = ("yes" if ok else "NO") if pos in POSITIONS else "-"
        print(f"{item['n']:>2} {data_iso[:4]:>4} {pos:>8} {mark}")
    print(f"\npositions with a grounded quote: {dict(grounded)}; quotes rejected: {rejected}")
    found = [p for p in POSITIONS if grounded[p] >= 1]
    verdict = (
        "PASS: at least 2 positions observed" if len(found) >= 2 else "FAIL: fewer than 2 positions"
    )
    print(verdict)
    return 0 if len(found) >= 2 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack")
    p.add_argument("-n", type=int, default=20)
    p.add_argument("-q", choices=sorted(QUESTIONS), default="q3")
    c = sub.add_parser("check")
    c.add_argument("-q", choices=sorted(QUESTIONS), default="q3")
    c.add_argument("answer", type=Path, help="file with the model's JSON answer")
    args = ap.parse_args()
    return (
        pack(args.db, args.n, args.q) if args.cmd == "pack" else check(args.db, args.answer, args.q)
    )


if __name__ == "__main__":
    sys.exit(main())
