"""`make index` entry point (HUMAN-run). Blocked until the index parser exists (ROADMAP T1.2),
which needs HTML fixtures saved by the owner (ROADMAP M1, HUMAN task)."""

import sys


def main() -> int:
    print("make index is not implemented yet: needs saved index-page fixtures and the parser (M1).")
    return 2


if __name__ == "__main__":
    sys.exit(main())
