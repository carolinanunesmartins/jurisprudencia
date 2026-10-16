"""Search normaliser v1. The TypeScript twin in web/src must give the same tokens: both are
checked against pipeline/tests/regression/golden/search_normalise.json."""

import re
import unicodedata
from collections import Counter
from pathlib import Path

MAX_TOKEN = 30
_TOKEN = re.compile(r"[a-z0-9]+")


def _load_stopwords() -> frozenset[str]:
    lines = (Path(__file__).parent / "stopwords.txt").read_text(encoding="utf-8").splitlines()
    return frozenset(w.strip() for w in lines if w.strip() and not w.startswith("#"))


STOPWORDS = _load_stopwords()


def normalise(text: str) -> list[str]:
    # º/ª are separators (442º = 442.º); marks go by category M, like JS \p{M}
    text = text.replace("º", " ").replace("ª", " ")
    folded = "".join(
        c
        for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.category(c).startswith("M")
    ).lower()
    return [
        t
        for t in _TOKEN.findall(folded)
        if (len(t) >= 2 or t.isdigit()) and len(t) <= MAX_TOKEN and t not in STOPWORDS
    ]


def term_counts(text: str) -> dict[str, int]:
    return dict(sorted(Counter(normalise(text)).items()))
