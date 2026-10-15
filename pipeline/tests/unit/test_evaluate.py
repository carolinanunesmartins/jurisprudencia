import pytest

from juris.evaluate.baseline import predict

pytestmark = pytest.mark.unit


def test_baseline_needs_the_question_pool():
    assert predict("q3", "basta a mora", in_pool=False) == "nao_decide"


def test_baseline_takes_the_one_position_whose_cue_occurs():
    assert predict("q6", "O prazo é absolutamente fixo.", True) == "absoluto"
    assert predict("q10", "A presunção é ilidível.", True) == "admissivel"


def test_baseline_ignores_a_negated_cue_and_abstains_on_both_or_none():
    assert (
        predict("q3", "Não basta a mora; só o incumprimento definitivo.", True)
        == "exige_definitivo"
    )
    assert predict("q6", "prazo relativo ou prazo absoluto", True) == "nao_decide"
    assert predict("q7", "nada a ver", True) == "nao_decide"


def test_score_counts_exact_recall_and_precision():
    from juris.evaluate.__main__ import _n, score

    pairs = [("a", "a"), ("a", "nao_decide"), ("nao_decide", "b"), ("nao_decide", "nao_decide")]
    assert score(pairs) == {"exact": (2, 4), "recall": (1, 2), "precision": (1, 2)}
    assert _n(1607043) == "1 607 043" and _n(3.98, 2) == "3,98"


def test_precision_section_counts_labels_of_shown_divergences():
    from juris.evaluate.__main__ import precision_section

    def row(shown, label, notes=""):
        return {
            "question": "q8",
            "type": "split",
            "window": "2014-2024",
            "shown": shown,
            "label": label,
            "notes": notes,
        }

    assert "Pendente" in "\n".join(precision_section([]))
    text = "\n".join(
        precision_section(
            [row("yes", "correct"), row("yes", "incorrect", "outro tema"), row("yes", "unclear")]
        )
    )
    assert "| mostradas no sítio (3) | 1 | 1 | 0 | 1 | 1/2 (50 %) |" in text
    assert "outro tema" in text
