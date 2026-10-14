"""M1.5 feasibility spike helpers (ROADMAP M1.5). Offline: no network, no API key.

  pack   pick ~20 pilot judgments for seed question 3 (sinal e mora) and write a prompt file
         the owner pastes into any LLM chat (HUMAN-run).
  check  read the model's JSON answer, verify every quote against the stored sumário
         (AGENTS.md rule 4) and print the positions found per year.

Everything lands in data/spike/ (gitignored: it contains sumários).
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

from juris.classify.grounding import is_grounded
from juris.db.subset import fold

PROMPT = Path(__file__).parent.parent / "juris" / "llm" / "prompts" / "spike_q3_v0.md"
OUT = Path("data/spike")
POSITIONS = ("A", "B")


def is_candidate(sumario: str) -> bool:
    text = fold(sumario)
    return "SINAL" in text and ("MORA" in text or "DEFINITIV" in text)


def pick(rows: list[tuple[str, str, str, str]], n: int) -> list[tuple[str, str, str, str]]:
    """Evenly spaced by date over the candidates, so the sample spans the whole period."""
    cands = sorted((r for r in rows if r[3] and is_candidate(r[3])), key=lambda r: (r[2], r[0]))
    if len(cands) <= n:
        return cands
    step = (len(cands) - 1) / (n - 1)
    return [cands[round(i * step)] for i in range(n)]


def pack(db: Path, n: int) -> int:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT doc_id, processo, data_iso, sumario FROM acordao WHERE fetched_at IS NOT NULL"
    ).fetchall()
    chosen = pick(rows, n)
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [PROMPT.read_text(encoding="utf-8")]
    for i, (_, processo, data_iso, sumario) in enumerate(chosen, 1):
        parts.append(f"\n### Acórdão {i}\nProcesso {processo} · {data_iso}\n\n{sumario}\n")
    (OUT / "pack.md").write_text("\n".join(parts), encoding="utf-8")
    (OUT / "ids.json").write_text(json.dumps([r[0] for r in chosen]), encoding="utf-8")
    print(f"{len(chosen)} judgments ({len(rows)} fetched) -> {OUT / 'pack.md'}")
    print("years:", ", ".join(r[2][:4] for r in chosen))
    return 0


def check(db: Path, answer: Path) -> int:
    ids = json.loads((OUT / "ids.json").read_text(encoding="utf-8"))
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
    c = sub.add_parser("check")
    c.add_argument("answer", type=Path, help="file with the model's JSON answer")
    args = ap.parse_args()
    return pack(args.db, args.n) if args.cmd == "pack" else check(args.db, args.answer)


if __name__ == "__main__":
    sys.exit(main())
