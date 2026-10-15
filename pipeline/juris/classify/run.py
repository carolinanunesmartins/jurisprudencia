"""Per-judgment classification (SPEC §6.1, ADR 0007): one call per judgment, all approved questions.

Input is the header plus the sumário; only judgments without a sumário send the full text,
truncated. Every quote is checked against the text that was sent: a quote that is not a verbatim
substring is stored as relevant=0, quote_ok=0 and counted (AGENTS.md rule 4).
"""

import csv
import json
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from juris.classify.grounding import ground
from juris.classify.schema import SchemaError, validate_answer
from juris.crawl.fetch import select_pilot
from juris.db.subset import subset_ids
from juris.llm.prompt import CLASSIFY, classify_prompt
from juris.llm.provider import LlmProvider, MissingFixture, Truncated, tokens_used
from juris.taxonomy.model import Taxonomy

TEXT_CHARS = 24_000  # ≈ 6 000 tokens of Portuguese prose (SPEC §6.1)
PILOT_SEED = 20261016


@dataclass
class Stats:
    judgments: int = 0
    schema_failures: int = 0
    truncated: int = 0
    stopped_by_budget: bool = False
    missing_fixtures: int = 0
    quotes_accepted: int = 0
    quotes_rejected: int = 0
    repairs: Counter[str] = field(default_factory=Counter)
    by_source: Counter[str] = field(default_factory=Counter)
    positions: Counter[tuple[str, str]] = field(default_factory=Counter)

    def report(self) -> str:
        lines = [
            f"judgments classified: {self.judgments} {dict(self.by_source)}",
            f"schema failures (after one retry): {self.schema_failures}",
            f"answers cut at max_tokens (not retried): {self.truncated}",
            f"missing replay fixtures: {self.missing_fixtures}",
            f"quotes accepted: {self.quotes_accepted}; rejected: {self.quotes_rejected}",
            f"  how accepted quotes were matched: {dict(sorted(self.repairs.items()))}",
        ]
        if self.stopped_by_budget:
            lines.append("STOPPED: token budget reached; run again to continue")
        lines += [f"  {q} {p}: {n}" for (q, p), n in sorted(self.positions.items())]
        return "\n".join(lines)


def build_input(row: sqlite3.Row) -> tuple[str, str, str]:
    """(input text for the model, text_source, the text quotes must come from)."""
    if row["sumario"]:
        source, text = "sumario", row["sumario"]
    else:
        source, text = "texto", row["texto"][:TEXT_CHARS]
    descritores = "; ".join(json.loads(row["descritores_json"] or "[]"))
    header = [
        f"Processo: {row['processo']}",
        f"Data: {row['data_iso']}",
        f"Secção: {row['secao'] or ''}",
        f"Relator: {row['relator'] or ''}",
        f"Meio processual: {row['meio_processual'] or ''}",
        f"Descritores: {descritores}",
        f"Fonte: {'sumário' if source == 'sumario' else 'texto integral (excerto)'}",
    ]
    return "\n".join(header) + "\n\n" + text, source, text


def eligible(conn: sqlite3.Connection) -> set[str]:
    have_text = {
        r[0]
        for r in conn.execute(
            "SELECT doc_id FROM acordao"
            " WHERE COALESCE(sumario, '') <> '' OR COALESCE(texto, '') <> ''"
        )
    }
    return subset_ids(conn) & have_text


def done_ids(conn: sqlite3.Connection, prompt_version: str) -> set[str]:
    return {
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT doc_id FROM classification WHERE prompt_version = ?", (prompt_version,)
        )
    }


def labels_filled(path: Path) -> tuple[int, int]:
    """(filled, total) rows of the blind label sheet; (0, 0) if it does not exist."""
    if not path.exists():
        return 0, 0
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return sum(1 for r in rows if (r.get("label") or "").strip()), len(rows)


def classify_one(
    provider: LlmProvider, tax: Taxonomy, system: str, row: sqlite3.Row, stats: Stats
) -> list[tuple] | None:
    """Rows for the classification table, or None when the judgment could not be classified."""
    prompt_input, source, text = build_input(row)
    answers = None
    for _ in range(2):  # one retry, on schema failure only (SPEC §6.1)
        try:
            answers = validate_answer(provider.generate_json(CLASSIFY, system, prompt_input), tax)
            break
        except Truncated:
            stats.truncated += 1  # a retry would be cut again and paid twice
            return None
        except (SchemaError, ValueError):
            continue
    if answers is None:
        stats.schema_failures += 1
        return None
    now = datetime.now(UTC).isoformat(timespec="seconds")
    out = []
    for qid, a in answers.items():
        relevant, quote_ok, quote = a.relevant, False, a.quote
        if relevant:
            span, how = ground(a.quote, text)
            quote_ok = span is not None
            if span is not None:
                quote = span  # the text's own words, never the model's copy
                stats.quotes_accepted += 1
                stats.repairs.update(how)
                stats.positions[(qid, a.position_id or "")] += 1
            else:
                stats.quotes_rejected += 1
                relevant = False
        out.append(
            (
                row["doc_id"],
                qid,
                int(relevant),
                a.position_id if relevant else None,
                quote,
                int(quote_ok),
                a.note,
                source,
                provider.model,
                CLASSIFY,
                now,
            )
        )
    stats.judgments += 1
    stats.by_source[source] += 1
    return out


def run(
    conn: sqlite3.Connection,
    provider: LlmProvider,
    tax: Taxonomy,
    pilot: int | None = None,
    limit: int | None = None,
    budget_tokens: int | None = None,
    progress_every: int = 50,
    reground: bool = False,
) -> Stats:
    """Classify the judgments not yet done; with `reground`, redo the ones already done (from
    replay fixtures, so no API calls) to apply a change in grounding."""
    conn.row_factory = sqlite3.Row
    pool = eligible(conn)
    ids = select_pilot(conn, pilot, PILOT_SEED, population=pool) if pilot else sorted(pool)
    done = done_ids(conn, CLASSIFY)
    todo = [d for d in ids if (d in done) == reground][:limit]
    system = classify_prompt(tax)
    stats = Stats()
    for i, doc_id in enumerate(todo, 1):
        if budget_tokens is not None and tokens_used(provider) >= budget_tokens:
            stats.stopped_by_budget = True
            break
        if progress_every and i % progress_every == 0:
            print(f"{i}/{len(todo)} judgments, {tokens_used(provider)} tokens so far", flush=True)
        row = conn.execute("SELECT * FROM acordao WHERE doc_id = ?", (doc_id,)).fetchone()
        try:
            rows = classify_one(provider, tax, system, row, stats)
        except MissingFixture:
            stats.missing_fixtures += 1
            continue
        if rows:
            conn.executemany(
                "INSERT OR REPLACE INTO classification(doc_id, question_id, relevant, position_id,"
                " quote, quote_ok, note, text_source, model, prompt_version, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
            conn.commit()
    return stats
