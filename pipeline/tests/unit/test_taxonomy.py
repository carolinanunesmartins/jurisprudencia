from pathlib import Path

import pytest
from pydantic import ValidationError

from juris.taxonomy.model import DEFAULT_PATH, Taxonomy, load_taxonomy

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[3]


def question(qid="q", positions=("a", "b")):
    return {
        "id": qid,
        "title_pt": "t",
        "description_pt": "d",
        "norms": [],
        "positions": [{"id": p, "label_pt": p, "definition_pt": p} for p in positions],
        "seed_source": "s",
        "status": "seed",
    }


def test_committed_seed_taxonomy_is_valid():
    tax = load_taxonomy(ROOT / DEFAULT_PATH)
    assert [q.id for q in tax.questions] == ["q1", "q2", "q3", "q4", "q5"]


def test_needs_two_positions():
    with pytest.raises(ValidationError):
        Taxonomy.model_validate({"version": "v", "questions": [question(positions=("a",))]})


def test_duplicate_question_ids_and_reserved_position_are_rejected():
    with pytest.raises(ValidationError):
        Taxonomy.model_validate({"version": "v", "questions": [question("x"), question("x")]})
    with pytest.raises(ValidationError):
        Taxonomy.model_validate(
            {"version": "v", "questions": [question(positions=("a", "nao_decide"))]}
        )
