"""Judge pass (SPEC §6.4) and rule confidence (§6.5) over the divergence table.

`make judge` (HUMAN-run, needs LLM_API_KEY and JUDGE_MODEL) or `make judge-replay` (offline).

The judge sees only the question, the two quotes, their dates and assigned positions. Verdicts
are cached as replay fixtures, so re-running `make detect` and the judge costs nothing twice.
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from juris.db.schema import connect
from juris.llm.prompt import PROMPTS
from juris.llm.provider import AnthropicProvider, LlmProvider, MissingFixture, ReplayProvider
from juris.taxonomy.model import Taxonomy, load_taxonomy

JUDGE = "judge_v1"
MAX_JUDGED = 40


class Verdict(BaseModel):
    model_config = ConfigDict(extra="ignore")
    real_opposition: bool
    legislative_change_possible: bool
    rationale: str = Field(default="", max_length=2000)
    confidence: Literal["alta", "media", "baixa"]


class CachedProvider:
    """Replay first, live only on a cache miss (the live provider records what it gets)."""

    def __init__(self, replay: ReplayProvider, live: LlmProvider):
        self.replay, self.live, self.model = replay, live, live.model

    def generate_json(self, prompt_id: str, system: str, input: str) -> dict[str, Any]:
        try:
            return self.replay.generate_json(prompt_id, system, input)
        except MissingFixture:
            return self.live.generate_json(prompt_id, system, input)


def strength(support: dict[str, int], pair_positions: list[str]) -> tuple[int, int]:
    """Weaker side first, then total: a 3-vs-3 split outranks 9-vs-2."""
    sides = [support.get(p, 0) for p in pair_positions]
    return (min(sides), sum(sides))


def rule_confidence(support: dict[str, int], pair_positions: list[str], agrees: bool) -> str:
    weaker = min(support.get(p, 0) for p in pair_positions)
    if agrees and weaker >= 3:
        return "alta"
    if agrees and weaker >= 2:
        return "media"
    return "baixa"


def judge_input(tax: Taxonomy, qid: str, pair: list[dict]) -> str:
    q = next(q for q in tax.questions if q.id == qid)
    lines = [f"Pergunta: {q.title_pt}. {q.description_pt}", "", "Posições:"]
    lines += [f"- {p.id}: {p.definition_pt}" for p in q.positions]
    for label, p in zip(("A", "B"), pair, strict=True):
        lines += [
            "",
            f"Excerto {label} ({p['date']}, posição atribuída: {p['position']}):",
            p["quote"],
        ]
    return "\n".join(lines)


def run(
    conn: sqlite3.Connection, provider: LlmProvider, tax: Taxonomy, system: str
) -> dict[str, int]:
    rows = conn.execute(
        "SELECT id, question_id, evidence_json FROM divergence WHERE type IN ('split', 'shift')"
    ).fetchall()
    ranked = []
    for div_id, qid, ev in rows:
        evidence = json.loads(ev)
        positions = [p["position"] for p in evidence["pair"]]
        ranked.append((strength(evidence["support"], positions), div_id, qid, evidence, positions))
    ranked.sort(key=lambda r: (r[0], -r[1]), reverse=True)
    stats = {"judged": 0, "not_judged": max(0, len(ranked) - MAX_JUDGED), "invalid": 0}
    for _, div_id, qid, evidence, positions in ranked[:MAX_JUDGED]:
        raw = provider.generate_json(JUDGE, system, judge_input(tax, qid, evidence["pair"]))
        try:
            verdict = Verdict.model_validate(raw)
        except ValidationError:
            stats["invalid"] += 1
            continue
        conf = rule_confidence(evidence["support"], positions, verdict.real_opposition)
        conn.execute(
            "UPDATE divergence SET judge_json = ?, rule_confidence = ? WHERE id = ?",
            (verdict.model_dump_json(), conf, div_id),
        )
        stats["judged"] += 1
    conn.commit()
    return stats


def display(verdict: Verdict | None) -> str | None:
    """SPEC §6.4: which label the UI shows; None = hidden (counted in the report)."""
    if verdict is None or not verdict.real_opposition:
        return None
    return "possivel_alteracao_legislativa" if verdict.legislative_change_possible else "mudanca"


def gate_g3(conn: sqlite3.Connection, dev: tuple[str, ...] = ("q2", "q3")) -> int:
    """SPEC §2 Gate G3: split/shift on a test question with real_opposition from the judge."""
    if not conn.execute("SELECT 1 FROM classification LIMIT 1").fetchone():
        print("Gate G3: not decidable yet, nothing is classified (run `make classify`)")
        return 0
    n = 0
    for qid, kind, start, end, judge in conn.execute(
        "SELECT question_id, type, window_start, window_end, judge_json FROM divergence"
        " WHERE type IN ('split', 'shift') ORDER BY question_id, window_start"
    ):
        verdict = Verdict.model_validate_json(judge) if judge else None
        shown = display(verdict)
        print(f"{qid} {kind} {start}-{end}: {shown or 'hidden'}")
        if qid not in dev and verdict and verdict.real_opposition:
            n += 1
    verdict_text = "STAY on contrato-promessa" if n >= 1 else "PIVOT to arrendamento urbano"
    print(f"\nGate G3: {n} judge-confirmed split/shift on test questions -> {verdict_text}")
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", choices=["live", "replay"], required=True)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    ap.add_argument("--replay-dir", type=Path, default=Path("data/replay"))
    a = ap.parse_args()
    replay = ReplayProvider(a.replay_dir)
    provider: LlmProvider = replay
    if a.provider == "live":
        key, model = os.environ.get("LLM_API_KEY"), os.environ.get("JUDGE_MODEL")
        if not key or not model:
            print("set LLM_API_KEY and JUDGE_MODEL (see .env.example)", file=sys.stderr)
            return 2
        provider = CachedProvider(replay, AnthropicProvider(key, model, record=a.replay_dir))
    system = (PROMPTS / f"{JUDGE}.md").read_text(encoding="utf-8")
    conn = connect(a.db)
    try:
        print(run(conn, provider, load_taxonomy(a.taxonomy), system))
    except MissingFixture as e:
        print(f"no replay fixture for a divergence ({e}); run `make judge` live first")
        return 1
    gate_g3(conn)
    return 0


if __name__ == "__main__":
    sys.exit(main())
