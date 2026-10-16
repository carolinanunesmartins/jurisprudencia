import json
from pathlib import Path

import pytest

from juris.db.schema import connect
from juris.db.snapshot import dump, load
from juris.export.__main__ import export
from juris.export.check import check
from juris.search.normalise import STOPWORDS, term_counts
from tests.unit.test_export import TAX, make_db

pytestmark = pytest.mark.unit

NO_AUJ = Path("no-such-auj.json")


def test_term_counts_are_sorted_counts_without_stopwords():
    counts = term_counts("A mora e a MORA; sinal do sinal, posse")
    assert counts == {"mora": 2, "posse": 1, "sinal": 2}
    assert list(counts) == sorted(counts)
    assert "de" in STOPWORDS and "a" not in term_counts("a")


def _search(out: Path) -> dict:
    return json.loads((out / "search.json").read_text(encoding="utf-8"))


def test_export_writes_a_deterministic_index_of_published_judgments(tmp_path):
    conn = make_db(tmp_path)
    export(conn, TAX, tmp_path / "a", auj=NO_AUJ)
    export(conn, TAX, tmp_path / "b", auj=NO_AUJ)
    raw = (tmp_path / "a" / "search.json").read_text(encoding="utf-8")
    assert raw == (tmp_path / "b" / "search.json").read_text(encoding="utf-8")
    index = _search(tmp_path / "a")
    assert index["docs"] == ["a", "b"]
    assert index["terms"]["relativo"] == [[0, 1]] and index["terms"]["prazo"] == [[0, 1], [1, 1]]
    assert index["lengths"] == [
        sum(tf for p in index["terms"].values() for i, tf in p if i == n) for n in (0, 1)
    ]
    assert "Texto integral reservado" not in raw and "SECRET" not in raw
    assert check(tmp_path / "a", tmp_path / "t.db") == []


def test_a_judgment_without_sumario_has_no_terms(tmp_path):
    conn = make_db(tmp_path)
    conn.execute("UPDATE acordao SET sumario = NULL WHERE doc_id = 'b'")
    export(conn, TAX, tmp_path / "o", auj=NO_AUJ)
    index = _search(tmp_path / "o")
    assert index["docs"] == ["a", "b"] and index["lengths"][1] == 0


def test_snapshot_keeps_terms_but_never_the_sumario(tmp_path):
    conn = make_db(tmp_path)
    dump(conn, tmp_path / "snap", auj=NO_AUJ)
    raw = (tmp_path / "snap" / "acordao.jsonl").read_text(encoding="utf-8")
    assert "Texto integral" not in raw and "O prazo" not in raw
    rows = [json.loads(line) for line in raw.splitlines()]
    assert rows[0]["sumario_terms"] == term_counts("O prazo é relativo. Texto integral reservado.")
    load(tmp_path / "fresh.db", tmp_path / "snap")
    stored = (
        connect(tmp_path / "fresh.db")
        .execute("SELECT sumario_terms FROM acordao WHERE doc_id = 'a'")
        .fetchone()[0]
    )
    assert json.loads(stored) == rows[0]["sumario_terms"]


def test_fresh_clone_exports_the_same_index(tmp_path):
    conn = make_db(tmp_path)
    conn.execute("UPDATE acordao SET sumario = NULL WHERE doc_id = 'b'")
    conn.execute("UPDATE acordao SET sumario_terms = ? WHERE doc_id = 'b'", ('{"prazo":1}',))
    export(conn, TAX, tmp_path / "orig", auj=NO_AUJ)
    dump(conn, tmp_path / "snap", auj=NO_AUJ)
    load(tmp_path / "fresh.db", tmp_path / "snap")
    export(connect(tmp_path / "fresh.db"), TAX, tmp_path / "again", auj=NO_AUJ)
    assert (tmp_path / "orig" / "search.json").read_text(encoding="utf-8") == (
        tmp_path / "again" / "search.json"
    ).read_text(encoding="utf-8")


def test_check_catches_a_term_with_a_space_and_an_index_out_of_range(tmp_path):
    export(make_db(tmp_path), TAX, tmp_path / "o", auj=NO_AUJ)
    path = tmp_path / "o" / "search.json"
    index = _search(tmp_path / "o")
    index["terms"]["duas palavras"] = [[0, 1]]
    index["terms"]["longe"] = [[9, 1]]
    path.write_text(json.dumps(index), encoding="utf-8")
    errors = check(tmp_path / "o")
    assert any("bad term" in e for e in errors) and any("bad posting" in e for e in errors)
