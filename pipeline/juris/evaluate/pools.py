"""Keyword candidate pools per approved question (SPEC §9.1).

They drew the 60 evaluation labels (`pipeline/tools/labelsheet.py`) and define relevance for the
keyword baseline (SPEC §9.4). Fixed before any classification output existed.
"""

from collections.abc import Callable


def _has(t: str, *words: str) -> bool:
    return any(w in t for w in words)


# Candidate pools on accent-folded upper-case sumários. Noisy on purpose: nao_decide is a label.
POOLS: dict[str, Callable[[str], bool]] = {
    "q2": lambda t: "EXECUCAO ESPECIFICA" in t and _has(t, "MORA", "DEFINITIV"),
    "q3": lambda t: "SINAL" in t and _has(t, "MORA", "DEFINITIV"),
    "q6": lambda t: "PRAZO" in t and _has(t, "ABSOLUT", "RELATIV", "ESSENCIAL"),
    "q7": lambda t: "TRADICAO" in t and _has(t, "POSSE", "POSSUIDOR", "DETENTOR", "DETENCAO"),
    "q8": lambda t: "RETENCAO" in t and "CONSUMIDOR" in t,
    "q9": lambda t: "RETENCAO" in t and "HIPOTECA" in t,
    "q10": lambda t: "SINAL" in t and "EXECUCAO ESPECIFICA" in t,
}
