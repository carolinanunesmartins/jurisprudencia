"""Divergence detection (SPEC §6.2-6.3): pure functions over positioned judgments.

Sliding windows overlap, so one real split shows in several consecutive windows; those are
merged into one divergence. A shift is reported once per change of dominant position: between
the last window dominated by the old position and the first later window, starting after it
ends, dominated by the new one.
"""

import tomllib
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from juris.db.subset import fold

_UNIFORMIZACAO = "UNIFORMIZACAO DE JURISPRUDENCIA"
# the meio processual field is short and controlled; the source misspells the second word
# ("UNIFORMIZAÇÃO DE JURSIPRUDÊNCIA", AUJ 4/2014), so the first word is enough there
_MEIO_MARKER = "UNIFORMIZ"


@dataclass(frozen=True)
class Config:
    window_years: int = 3
    min_support: int = 2
    dominance: float = 0.60
    first_year: int = 2000
    last_year: int = 2025
    pair_rule: str = "v1"  # which judgments show a divergence to the judge (SPEC §6.2)


def load_config(path: Path) -> Config:
    return Config(**tomllib.loads(path.read_text(encoding="utf-8")))


@dataclass(frozen=True)
class Point:
    """One judgment's grounded position on one question."""

    doc_id: str
    date: str  # ISO
    position: str
    quote: str = ""
    url: str = ""
    uniformizacao: bool = False
    partial: bool = False  # the stored quote is part of what the model cited (trimmed, ellipsis)

    @property
    def year(self) -> int:
        return int(self.date[:4])


@dataclass
class Divergence:
    question_id: str
    type: str  # split | shift | resolved
    window_start: int
    window_end: int
    support: dict[str, int] = field(default_factory=dict)
    pair: list[Point] = field(default_factory=list)
    resolves: tuple[str, int, int] | None = None  # (type, start, end) of the divergence resolved

    def evidence(self) -> dict:
        return {
            "support": self.support,
            # `partial` steers the choice (pair rule v2); it is not evidence the judge sees
            "pair": [{k: v for k, v in asdict(p).items() if k != "partial"} for p in self.pair],
            "resolves": list(self.resolves) if self.resolves else None,
        }


def is_uniformizacao(meio_processual: str | None, texto: str | None) -> bool:
    """SPEC §6.3 heuristic: marker in meio processual or the first 2 000 characters of the text."""
    return _MEIO_MARKER in fold(meio_processual or "") or _UNIFORMIZACAO in fold(
        (texto or "")[:2000]
    )


def uniformizacao_of(flag: int | None, meio_processual: str | None, texto: str | None) -> bool:
    """The stored flag (snapshot databases have no text), else the heuristic."""
    return bool(flag) if flag is not None else is_uniformizacao(meio_processual, texto)


@dataclass(frozen=True)
class Window:
    start: int
    end: int
    counts: Counter[str]

    def dominant(self, cfg: Config) -> str | None:
        total = sum(self.counts.values())
        if not total:
            return None
        pos, n = max(self.counts.items(), key=lambda kv: (kv[1], kv[0]))
        winners = [p for p, c in self.counts.items() if c == n]
        if len(winners) > 1 or n / total < cfg.dominance or n < cfg.min_support:
            return None
        return pos

    def split_positions(self, cfg: Config) -> list[str]:
        return sorted(p for p, c in self.counts.items() if c >= cfg.min_support)


def windows(points: list[Point], cfg: Config) -> list[Window]:
    out = []
    for start in range(cfg.first_year, cfg.last_year - cfg.window_years + 2):
        end = start + cfg.window_years - 1
        out.append(
            Window(start, end, Counter(p.position for p in points if start <= p.year <= end))
        )
    return out


def _in(points: list[Point], start: int, end: int, position: str) -> list[Point]:
    return sorted(
        (p for p in points if start <= p.year <= end and p.position == position),
        key=lambda p: (p.date, p.doc_id),
    )


def splits(qid: str, points: list[Point], cfg: Config) -> list[Divergence]:
    """Consecutive windows where >= 2 positions reach k, merged into one divergence."""
    out: list[Divergence] = []
    for w in windows(points, cfg):
        if len(w.split_positions(cfg)) < 2:
            continue
        if out and w.start <= out[-1].window_end + 1:
            out[-1].window_end = w.end
        else:
            out.append(Divergence(qid, "split", w.start, w.end))
    for d in out:
        span = [p for p in points if d.window_start <= p.year <= d.window_end]
        support = Counter(p.position for p in span)
        d.support = dict(sorted(support.items()))
        # the two best-supported positions; A is the one that appears first in the span
        top = sorted(support, key=lambda pos: (-support[pos], pos))[:2]
        a_pts, b_pts = sorted(
            (_in(span, d.window_start, d.window_end, pos) for pos in top),
            key=lambda pts: (pts[0].date, pts[0].doc_id),
        )
        b0 = b_pts[0]
        # v1: latest A judgment up to the first B judgment vs that first B judgment
        d.pair = [[p for p in a_pts if (p.date, p.doc_id) <= (b0.date, b0.doc_id)][-1], b0]
        if cfg.pair_rule == "v2":
            d.pair = _closest_whole_pair(a_pts, b_pts) or d.pair
    return out


def _closest_whole_pair(a_pts: list[Point], b_pts: list[Point]) -> list[Point] | None:
    """v2: the A and B judgments closest in time, both with a whole (not partial) quote."""
    a_ok = [p for p in a_pts if not p.partial]
    b_ok = [p for p in b_pts if not p.partial]
    if not a_ok or not b_ok:
        return None
    a, b = min(
        ((a, b) for a in a_ok for b in b_ok),
        key=lambda ab: (
            abs(date.fromisoformat(ab[0].date) - date.fromisoformat(ab[1].date)).days,
            min(ab[0].date, ab[1].date),
            ab[0].doc_id,
            ab[1].doc_id,
        ),
    )
    return sorted([a, b], key=lambda p: (p.date, p.doc_id))


def shifts(qid: str, points: list[Point], cfg: Config) -> list[Divergence]:
    dominated = [(w, d) for w in windows(points, cfg) if (d := w.dominant(cfg))]
    out: list[Divergence] = []
    last_old: Window | None = None
    old: str | None = None
    for w, pos in dominated:
        if old is None or pos == old:
            old, last_old = pos, w
            continue
        assert last_old is not None
        if w.start > last_old.end:
            before = _in(points, last_old.start, last_old.end, old)
            after = _in(points, w.start, w.end, pos)
            if cfg.pair_rule == "v2":  # skip partial quotes when a whole one exists
                before = [p for p in before if not p.partial] or before
                after = [p for p in after if not p.partial] or after
            out.append(
                Divergence(
                    qid,
                    "shift",
                    last_old.start,
                    w.end,
                    support={old: last_old.counts[old], pos: w.counts[pos]},
                    pair=[before[-1], after[0]],
                )
            )
            old, last_old = pos, w
        # else: the new position dominates an overlapping window; wait for a disjoint one
    return out


def resolved(qid: str, points: list[Point], found: list[Divergence]) -> list[Divergence]:
    """A uniformização judgment positioned on the question, inside or after a split/shift."""
    marked = sorted((p for p in points if p.uniformizacao), key=lambda p: (p.date, p.doc_id))
    out = []
    for d in found:
        hit = next((p for p in marked if p.year >= d.window_start), None)
        if hit:
            out.append(
                Divergence(
                    qid,
                    "resolved",
                    d.window_start,
                    hit.year,
                    support=d.support,
                    pair=[hit],
                    resolves=(d.type, d.window_start, d.window_end),
                )
            )
    return out


def detect(qid: str, points: list[Point], cfg: Config) -> list[Divergence]:
    found = splits(qid, points, cfg) + shifts(qid, points, cfg)
    return found + resolved(qid, points, found)
