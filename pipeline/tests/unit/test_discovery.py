import json
from pathlib import Path

import pytest

from juris.db.schema import connect
from tools import discovery

pytestmark = pytest.mark.unit

TAX = Path(__file__).resolve().parents[3] / "data" / "taxonomy.json"
S1 = "O sinal só se perde com incumprimento definitivo, não com a simples mora."
S2 = "Basta a mora do promitente para a execução específica."


def make_db(tmp_path):
    conn = connect(tmp_path / "t.db")
    for doc_id, year, sumario in (("d0", 2005, S1), ("d1", 2010, S2), ("d2", 2012, S2)):
        conn.execute(
            "INSERT INTO acordao(doc_id, processo, url, data_iso, sumario, fetched_at)"
            " VALUES (?,?,?,?,?,?)",
            (doc_id, "p", "u", f"{year}-01-01", sumario, "x"),
        )
    conn.commit()
    (tmp_path / "data" / "discovery").mkdir(parents=True)
    (tmp_path / "data" / "discovery" / "ids_1.json").write_text(json.dumps(["d0", "d1", "d2"]))
    return tmp_path / "t.db"


def answer(tmp_path, items):
    (tmp_path / "data" / "discovery" / "answer_1.json").write_text(
        json.dumps(items), encoding="utf-8"
    )


def known(question, position, quote):
    return {"pergunta": question, "posicao": position, "citacao": quote}


def test_questions_are_rendered_from_the_taxonomy():
    text = discovery.render_questions(TAX)
    assert "**q3**" in text and "`exige_definitivo`" in text


def test_check_counts_grounded_positions_and_new_questions(tmp_path, monkeypatch, capsys):
    db = make_db(tmp_path)
    monkeypatch.chdir(tmp_path)
    answer(
        tmp_path,
        [
            {
                "n": 1,
                "conhecidas": [known("q3", "exige_definitivo", "só se perde com incumprimento")],
                "novas": [{"titulo": "T?", "rotulo": "x", "citacao": "O sinal só se perde"}],
            },
            {
                "n": 2,
                "conhecidas": [known("q3", "basta_mora", "Basta a mora do promitente")],
                "novas": [{"titulo": "T?", "rotulo": "y", "citacao": "frase inventada"}],
            },
            {"n": 3, "conhecidas": [known("q9", "z", "x")], "novas": []},
        ],
    )
    rc = discovery.check(db, TAX, 1)
    out = capsys.readouterr().out
    assert "quotes rejected: 1; invalid ids: 1" in out
    assert "exige_definitivo" in out and "basta_mora" in out
    assert "1 seed + 0 proposed" in out and rc == 1
