"""`make classify` (HUMAN-run, live) and `make classify-replay` (offline); see classify.run."""

import argparse
import os
import sys
from pathlib import Path

from juris.classify.run import labels_filled, run
from juris.db.schema import connect
from juris.llm.provider import AnthropicProvider, ApiError, ReplayProvider
from juris.taxonomy.model import load_taxonomy

LABELS = Path("data/eval/labels.csv")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--provider", choices=["live", "replay"], required=True)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    ap.add_argument("--replay-dir", type=Path, default=Path("data/replay"))
    ap.add_argument("--pilot", type=int, help="stratified random sample of N subset judgments")
    ap.add_argument("--limit", type=int, help="stop after N judgments")
    ap.add_argument(
        "--budget-tokens",
        type=int,
        default=3_000_000,
        help="stop when input+output tokens reach this (about 2x the full-run estimate)",
    )
    ap.add_argument(
        "--not-blind",
        action="store_true",
        help="allow a live run before the 60 labels are filled (breaks the blind evaluation)",
    )
    a = ap.parse_args()
    tax = load_taxonomy(a.taxonomy)
    if a.provider == "replay":
        provider = ReplayProvider(a.replay_dir)
    else:
        filled, total = labels_filled(LABELS)
        if (total == 0 or filled < total) and not a.not_blind:
            print(
                f"{LABELS}: {filled}/{total} labels filled. Label and commit them before any live"
                " run (SPEC §9.1, ROADMAP M4), or pass --not-blind.",
                file=sys.stderr,
            )
            return 2
        key, model = os.environ.get("LLM_API_KEY"), os.environ.get("CLASSIFY_MODEL")
        if not key or not model:
            print("set LLM_API_KEY and CLASSIFY_MODEL (see .env.example)", file=sys.stderr)
            return 2
        provider = AnthropicProvider(
            key, model, record=a.replay_dir, workspace_id=os.environ.get("LLM_WORKSPACE_ID")
        )
    try:
        stats = run(
            connect(a.db),
            provider,
            tax,
            pilot=a.pilot,
            limit=a.limit,
            budget_tokens=a.budget_tokens,
        )
    except ApiError as e:
        # judgments finished before the error are stored; re-running resumes (runbook §5)
        print(f"{e}\nStopped. See docs/llm-runbook.md §5, then re-run.", file=sys.stderr)
        return 1
    print(stats.report())
    if isinstance(provider, AnthropicProvider):
        print(f"tokens: {provider.usage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
