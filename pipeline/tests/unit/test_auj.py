import json

import pytest

from juris.export.__main__ import export
from juris.export.check import check
from tests.unit.test_export import TAX, make_db

pytestmark = pytest.mark.unit


def card(quote_b="O prazo é absoluto"):
    return [
        {
            "id": "auj-x",
            "doc_id": "a",
            "related_questions": ["q6"],
            "question_quote": None,
            "conflict_quote": "O prazo é relativo",
            "sides": [
                {"auj_quote": "O prazo é", "judgments": [{"doc_id": "b", "quote": quote_b}]},
                {"auj_quote": "relativo", "judgments": []},
            ],
            "ruling_quote": "Texto integral reservado.",
        }
    ]


def run(tmp_path, cards):
    conn = make_db(tmp_path)
    (tmp_path / "auj.json").write_text(json.dumps(cards, ensure_ascii=False), encoding="utf-8")
    export(conn, TAX, tmp_path / "out", auj=tmp_path / "auj.json")
    return json.loads((tmp_path / "out" / "aujs.json").read_text(encoding="utf-8"))


def test_auj_cards_get_processo_date_and_link_from_the_database(tmp_path):
    (a,) = run(tmp_path, card())
    assert (a["processo"], a["date"]) == ("a/10", "2010-03-01")
    assert a["sides"][0]["judgments"][0]["url"].startswith("https://www.dgsi.pt/")


def test_data_check_rejects_an_auj_quote_that_is_not_in_the_judgment(tmp_path):
    run(tmp_path, card(quote_b="O prazo é sempre essencial"))
    errors = check(tmp_path / "out", tmp_path / "t.db")
    assert any("auj auj-x: quote not grounded in b" in e for e in errors)
    (tmp_path / "ok").mkdir()
    run(tmp_path / "ok", card())
    assert check(tmp_path / "ok" / "out", tmp_path / "ok" / "t.db") == []


def test_an_auj_card_referring_to_an_unknown_judgment_fails_the_export(tmp_path):
    bad = card()
    bad[0]["sides"][0]["judgments"][0]["doc_id"] = "zzz"
    with pytest.raises(LookupError):
        run(tmp_path, bad)
