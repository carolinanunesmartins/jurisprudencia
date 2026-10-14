import json

import pytest

from juris.db.schema import connect
from tools import spike

pytestmark = pytest.mark.unit

SUM_A = "Basta a mora do promitente para exigir o sinal em dobro."
SUM_B = "O sinal só se perde com incumprimento definitivo, não com a simples mora."


def rows(n: int):
    return [(f"d{i:02}", f"{i}/20", f"{2000 + i}-01-01", SUM_A) for i in range(n)]


def test_candidates_need_sinal_and_mora_or_definitivo():
    assert spike.is_candidate("Sinal e MORA do promitente")
    assert spike.is_candidate("sinal; incumprimento definitivo")
    assert not spike.is_candidate("Execução específica e mora")
    assert not spike.is_candidate("Contrato de trabalho sinalagmático")


def test_pick_spreads_over_the_whole_period_and_is_deterministic():
    chosen = spike.pick(rows(25), 5)
    assert [r[0] for r in chosen] == ["d00", "d06", "d12", "d18", "d24"]
    assert spike.pick(rows(25), 5) == chosen


def test_pick_returns_everything_when_fewer_candidates_than_asked():
    assert len(spike.pick(rows(3) + [("x", "p", "2001-01-01", "sem tema")], 20)) == 3


def make_db(tmp_path):
    conn = connect(tmp_path / "t.db")
    for doc_id, sumario in (("d0", SUM_A), ("d1", SUM_B), ("d2", SUM_A)):
        conn.execute(
            "INSERT INTO acordao(doc_id, processo, url, data_iso, sumario, fetched_at)"
            " VALUES (?,?,?,?,?,?)",
            (doc_id, "p", "u", "2010-05-05", sumario, "x"),
        )
    conn.commit()
    (tmp_path / "data" / "spike").mkdir(parents=True)
    (tmp_path / "data" / "spike" / "ids_q3.json").write_text(json.dumps(["d0", "d1", "d2"]))
    return tmp_path / "t.db"


def answer(tmp_path, items):
    p = tmp_path / "ans.json"
    p.write_text("```json\n" + json.dumps(items) + "\n```", encoding="utf-8")
    return p


def test_check_passes_with_two_grounded_positions(tmp_path, monkeypatch, capsys):
    db = make_db(tmp_path)
    monkeypatch.chdir(tmp_path)
    items = [
        {"n": 1, "posicao": "A", "citacao": "Basta a mora do promitente"},
        {"n": 2, "posicao": "B", "citacao": "só se perde com incumprimento  definitivo"},
        {"n": 3, "posicao": "nenhuma", "citacao": ""},
    ]
    assert spike.check(db, answer(tmp_path, items)) == 0
    assert "PASS" in capsys.readouterr().out


def test_check_rejects_invented_quotes_and_fails_with_one_position(tmp_path, monkeypatch, capsys):
    db = make_db(tmp_path)
    monkeypatch.chdir(tmp_path)
    items = [
        {"n": 1, "posicao": "A", "citacao": "Basta a mora do promitente"},
        {"n": 2, "posicao": "B", "citacao": "frase que não existe no sumário"},
    ]
    assert spike.check(db, answer(tmp_path, items)) == 1
    out = capsys.readouterr().out
    assert "quotes rejected: 1" in out and "FAIL" in out


def test_q1_and_q2_candidates():
    assert spike.is_candidate("Execução específica; alienação a terceiro", "q1")
    assert not spike.is_candidate("Execução específica e mora", "q1")
    assert spike.is_candidate("Execução específica; mora do promitente", "q2")
    assert not spike.is_candidate("Sinal e mora", "q2")
