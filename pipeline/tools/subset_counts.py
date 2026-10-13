"""T1.3 helper: numbers behind docs/adr/0005-subset.md, read straight from the index in SQLite.

Usage: uv run python pipeline/tools/subset_counts.py [--db data/juris.db]
Read-only. Prints per-year totals, candidate theme descriptors and the SPEC §2 subset size.
"""

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path

from juris.db.subset import FIRST_YEAR, LAST_YEAR, fold, in_subset, theme_descriptor

CANDIDATES = ("PROMESSA", "SINAL", "EXECUCAO ESPECIFICA", "CLAUSULA PENAL")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    args = ap.parse_args()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    rows = [
        (data_iso or "", json.loads(dj or "[]"))
        for data_iso, dj in conn.execute("SELECT data_iso, descritores_json FROM acordao")
    ]
    print(f"total judgments: {len(rows)}")

    per_year = Counter(d[:4] for d, _ in rows)
    print("\nall judgments per year:", ", ".join(f"{y}:{per_year[y]}" for y in sorted(per_year)))

    named: Counter[str] = Counter(
        desc for _, descs in rows for desc in descs if any(n in fold(desc) for n in CANDIDATES)
    )
    print(f"\ndescriptors containing {CANDIDATES} (substring, noisy): {len(named)}")
    for desc, n in named.most_common(40):
        print(f"  {n:>5}  {'[theme] ' if theme_descriptor(desc) else '        '}{desc}")

    subset = Counter(d[:4] for d, descs in rows if in_subset(d, descs))
    print(f"\nsubset (theme descriptors, {FIRST_YEAR}-{LAST_YEAR}): {sum(subset.values())}")
    print("  per year:", ", ".join(f"{y}:{subset[y]}" for y in sorted(subset)))
    recent = sum(n for y, n in subset.items() if y >= "2005")
    print(f"  restricted to 2005-{LAST_YEAR}: {recent}")


if __name__ == "__main__":
    main()
