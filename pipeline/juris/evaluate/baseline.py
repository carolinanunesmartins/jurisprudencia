"""Keyword baseline for position accuracy (SPEC §9.4), fixed 2026-10-15 before it was run.

A judgment is relevant to a question when its text is in that question's label pool (the
descriptor/keyword predicate that drew the 60 labels, `pipeline/tools/labelsheet.py`). Its
position is the one whose cue phrases (taken from the frozen position definitions, accent- and
case-insensitive) occur in the classifier's input text; cues of both positions, or of none,
give `nao_decide`; a cue right after "não" does not count. Deliberately naive: it is the floor
the LLM classifier has to beat.
"""

from juris.db.subset import fold

CUES: dict[str, dict[str, tuple[str, ...]]] = {
    "q2": {
        "basta_mora": ("BASTA A MORA", "BASTA A SIMPLES MORA", "MORA E SUFICIENTE"),
        "exige_definitivo": (
            "NAO BASTA A MORA",
            "NAO BASTANDO A MORA",
            "PRESSUPOE INCUMPRIMENTO DEFINITIVO",
        ),
    },
    "q3": {
        "basta_mora": ("BASTA A MORA", "BASTA A SIMPLES MORA", "MORA E SUFICIENTE"),
        "exige_definitivo": (
            "NAO BASTA A MORA",
            "NAO BASTANDO A MORA",
            "SO O INCUMPRIMENTO DEFINITIVO",
        ),
    },
    "q6": {
        "relativo": ("PRAZO RELATIVO", "RELATIVAMENTE FIXO", "TERMO RELATIVO"),
        "absoluto": ("PRAZO ABSOLUTO", "ABSOLUTAMENTE FIXO", "TERMO ESSENCIAL", "PRAZO ESSENCIAL"),
    },
    "q7": {
        "detentor": ("MERO DETENTOR", "DETENTOR PRECARIO", "POSSUIDOR PRECARIO", "EM NOME ALHEIO"),
        "possuidor": ("POSSE EM NOME PROPRIO", "VERDADEIRA POSSE", "VERDADEIRO POSSUIDOR"),
    },
    "q8": {
        "exige_consumidor": (
            "SEJA CONSUMIDOR",
            "SE TIVER A QUALIDADE DE CONSUMIDOR",
            "SO BENEFICIA",
        ),
        "nao_exige": ("NAO SE EXIGE", "INDEPENDENTEMENTE DA QUALIDADE DE CONSUMIDOR"),
    },
    "q9": {
        "prevalece": (
            "PREVALECE SOBRE A HIPOTECA",
            "SOBREPOE",
            "PREVALENCIA DO DIREITO DE RETENCAO",
        ),
        "nao_prevalece": ("NAO PREVALECE", "PREVALENCIA DA HIPOTECA", "NAO PODE OPOR"),
    },
    "q10": {
        "admissivel": ("ILIDIVEL", "PRESUNCAO RELATIVA", "NAO IMPEDE A EXECUCAO ESPECIFICA"),
        "afastada": (
            "CONVENCAO CONTRARIA",
            "AFASTA A EXECUCAO ESPECIFICA",
            "EXCLUI A EXECUCAO ESPECIFICA",
        ),
    },
}


def _hit(cues: tuple[str, ...], text: str) -> bool:
    """A cue counts unless that occurrence is negated ("NAO " right before it)."""
    for cue in cues:
        start = text.find(cue)
        while start >= 0:
            if not text[:start].endswith("NAO "):
                return True
            start = text.find(cue, start + 1)
    return False


def predict(question_id: str, text: str, in_pool: bool) -> str:
    if not in_pool:
        return "nao_decide"
    t = fold(text)
    (a, a_cues), (b, b_cues) = CUES[question_id].items()
    hit_a, hit_b = _hit(a_cues, t), _hit(b_cues, t)
    if hit_a == hit_b:
        return "nao_decide"
    return a if hit_a else b
