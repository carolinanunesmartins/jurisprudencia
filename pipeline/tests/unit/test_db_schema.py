import sqlite3

import pytest

from juris.db.schema import connect

pytestmark = pytest.mark.unit


def test_schema_creates_the_three_spec_tables(tmp_path):
    conn = connect(tmp_path / "t.db")
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"acordao", "classification", "divergence"} <= names


def test_classification_primary_key_is_processo_and_question(tmp_path):
    conn = connect(tmp_path / "t.db")
    conn.execute("INSERT INTO classification(processo, question_id, relevant) VALUES ('1','q1',1)")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO classification(processo, question_id, relevant) VALUES ('1','q1',0)"
        )
