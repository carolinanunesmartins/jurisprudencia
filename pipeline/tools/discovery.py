"""M3 discovery pass helpers (SPEC §5.3, gate G2). Offline: no network, no API key.

  pack   draw a random sample of fetched judgments (stratified by year, fixed seed), split it
         into parts the owner pastes into an LLM chat (HUMAN-run), data/discovery/pack_<k>.md.
  check  read the answers (answer_<k>.json), verify every quote against the stored sumário
         (AGENTS.md rule 4) and print, per known question, the positions observed (gate G2),
         plus the new questions proposed, for the owner to approve, edit or reject.

Everything lands in data/discovery/ (gitignored: it contains sumários).
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

from juris.classify.grounding import is_grounded
from juris.crawl.fetch import select_pilot
from juris.taxonomy.model import load_taxonomy

PROMPT = Path(__file__).parent.parent / "juris" / "llm" / "prompts" / "discovery_v0.md"
OUT = Path("data/discovery")
SEED = 20261015
G2_QUESTIONS, G2_POSITIONS = 3, 2


def render_questions(tax_path: Path) -> str:
    lines = []
    for q in load_taxonomy(tax_path).questions:
        lines.append(f"- **{q.id}** — {q.title_pt}. {q.description_pt}")
        lines += [f"  - `{p.id}`: {p.definition_pt}" for p in q.positions]
    return "\n".join(lines)


def pack(db: Path, tax: Path, size: int, parts: int) -> int:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    with_sumario = {r[0] for r in conn.execute("SELECT doc_id FROM acordao WHERE sumario <> ''")}
    ids = select_pilot(conn, size, SEED, population=with_sumario)
    OUT.mkdir(parents=True, exist_ok=True)
    head = PROMPT.read_text(encoding="utf-8").replace("{{QUESTIONS}}", render_questions(tax))
    per = -(-len(ids) // parts)
    for k in range(parts):
        chunk = ids[k * per : (k + 1) * per]
        body = [head]
        for i, doc_id in enumerate(chunk, 1):
            processo, data_iso, sumario = conn.execute(
                "SELECT processo, data_iso, sumario FROM acordao WHERE doc_id = ?", (doc_id,)
            ).fetchone()
            body.append(f"\n### Acórdão {i}\nProcesso {processo} · {data_iso}\n\n{sumario}\n")
        (OUT / f"pack_{k + 1}.md").write_text("\n".join(body), encoding="utf-8")
        (OUT / f"ids_{k + 1}.json").write_text(json.dumps(chunk), encoding="utf-8")
        print(f"part {k + 1}: {len(chunk)} judgments -> {OUT / f'pack_{k + 1}.md'}")
    return 0


def _load(path: Path):
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("```"):  # tolerate a fenced block around the JSON
        text = text.strip("`").removeprefix("json").strip()
    return json.loads(text)


def check(db: Path, tax: Path, parts: int) -> int:
    questions = {q.id: {p.id for p in q.positions} for q in load_taxonomy(tax).questions}
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    seen: dict[str, Counter[str]] = defaultdict(Counter)
    years: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    novas: dict[str, Counter[str]] = defaultdict(Counter)
    total = rejected = unknown = 0
    for k in range(1, parts + 1):
        ids = json.loads((OUT / f"ids_{k}.json").read_text(encoding="utf-8"))
        for item in _load(OUT / f"answer_{k}.json"):
            doc_id = ids[item["n"] - 1]
            data_iso, sumario = conn.execute(
                "SELECT data_iso, sumario FROM acordao WHERE doc_id = ?", (doc_id,)
            ).fetchone()
            total += 1
            for c in item.get("conhecidas", []):
                if c.get("posicao") not in questions.get(c.get("pergunta"), set()):
                    unknown += 1
                elif is_grounded(c.get("citacao", ""), sumario):
                    seen[c["pergunta"]][c["posicao"]] += 1
                    years[c["pergunta"]][c["posicao"]].add(data_iso[:4])
                else:
                    rejected += 1
            for n in item.get("novas", []):
                if is_grounded(n.get("citacao", ""), sumario):
                    novas[n["titulo"]][n.get("rotulo", "?")] += 1
                else:
                    rejected += 1
    print(f"{total} judgments answered; quotes rejected: {rejected}; invalid ids: {unknown}\n")
    ok = 0
    for qid in questions:
        pos = seen[qid]
        if len(pos) >= G2_POSITIONS:
            ok += 1
        spread = {p: f"{n} ({min(years[qid][p])}-{max(years[qid][p])})" for p, n in pos.items()}
        print(f"{qid}: {spread or 'no judgment'}")
    print("\nProposed new questions (quote-grounded):")
    for title, labels in sorted(novas.items(), key=lambda t: -sum(t[1].values())):
        print(f"- {title}  [{sum(labels.values())}] {dict(labels)}")
    new_ok = sum(1 for lab in novas.values() if len(lab) >= G2_POSITIONS)
    print(f"\nG2: {ok} seed + {new_ok} proposed questions show >= {G2_POSITIONS} positions")
    passed = ok + new_ok >= G2_QUESTIONS
    print("G2 PASS (owner still reviews the proposed ones)" if passed else "G2 FAIL: see SPEC §2")
    return 0 if passed else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack")
    p.add_argument("--size", type=int, default=150)
    p.add_argument("--parts", type=int, default=3)
    c = sub.add_parser("check")
    c.add_argument("--parts", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "pack":
        return pack(a.db, a.taxonomy, a.size, a.parts)
    return check(a.db, a.taxonomy, a.parts)


if __name__ == "__main__":
    sys.exit(main())
