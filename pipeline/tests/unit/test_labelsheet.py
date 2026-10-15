import csv
from pathlib import Path

import pytest

from juris.llm.prompt import classify_prompt
from juris.taxonomy.model import load_taxonomy
from tools import labelsheet

pytestmark = pytest.mark.unit

TAX = load_taxonomy(Path(__file__).resolve().parents[3] / "data" / "taxonomy.json")
SUMARIOS = {
    "q2": "A execução específica basta-se com a mora.",
    "q3": "O sinal só se perde com incumprimento definitivo.",
    "q6": "O prazo fixado é absoluto.",
    "q7": "Com a tradição, o promitente-comprador é mero detentor.",
    "q8": "O direito de retenção exige que seja consumidor.",
    "q9": "O direito de retenção prevalece sobre a hipoteca.",
    "q10": "O sinal não afasta a execução específica.",
}


def rows(per_question: int):
    out = []
    for q, text in SUMARIOS.items():
        for i in range(per_question):
            out.append((f"{q}-{i}", "p", "u", f"{2000 + i:04d}-01-01", text))
    return out


def test_draw_allocates_sixty_unique_rows():
    picked = labelsheet.draw(rows(12), TAX, seen=set())
    assert len(picked) == 60
    assert len({r[0] for _, r in picked}) == 60
    for q, n in labelsheet.ALLOCATION.items():
        assert sum(1 for x, _ in picked if x == q) == n


def test_draw_excludes_judgments_already_shown_with_model_output():
    seen = {f"q8-{i}" for i in range(12)}
    picked = labelsheet.draw(rows(12), TAX, seen=seen)
    assert not any(r[0] in seen for _, r in picked)


def test_spaced_spans_the_period():
    chosen = labelsheet.spaced([(str(i), "", "", f"{2000 + i}-01-01", "") for i in range(26)], 3)
    assert [r[3][:4] for r in chosen] == ["2000", "2012", "2025"]


def test_validate_flags_labels_outside_the_question(tmp_path, capsys):
    path = tmp_path / "labels.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(labelsheet.FIELDS)
        w.writerow([1, "d", "p", "2000-01-01", "u", "q3", "exige_definitivo", ""])
        w.writerow([2, "d", "p", "2000-01-01", "u", "q6", "unclear", ""])
        w.writerow([3, "d", "p", "2000-01-01", "u", "q7", "basta_mora", ""])
        w.writerow([4, "d", "p", "2000-01-01", "u", "q8", "", ""])
    rc = labelsheet.validate(Path(__file__).resolve().parents[3] / "data" / "taxonomy.json", path)
    assert rc == 1 and "3 labels filled, 1 invalid" in capsys.readouterr().out


def test_classify_prompt_lists_only_approved_questions():
    text = classify_prompt(TAX)
    assert "**q3**" in text and "**q10**" in text
    assert "**q1**" not in text and "**q4**" not in text and "{{QUESTIONS}}" not in text
