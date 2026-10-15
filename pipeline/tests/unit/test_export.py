import json
from pathlib import Path

import pytest

from juris.db.schema import connect
from juris.export.__main__ import export
from juris.export.check import check

pytestmark = pytest.mark.unit

NO_AUJ = Path("no-such-auj.json")  # the real AUJ cards refer to judgments not in test DBs

TAX = Path(__file__).resolve().parents[3] / "data" / "taxonomy.json"
URL = "https://www.dgsi.pt/jstj.nsf/x/{}?OpenDocument"
DESC = json.dumps(["CONTRATO-PROMESSA"])
VERDICT = {
    "real_opposition": True,
    "legislative_change_possible": False,
    "rationale": "opostos",
    "confidence": "media",
}


def make_db(tmp_path):
    conn = connect(tmp_path / "t.db")
    for doc_id, year, pos, ok in (
        ("a", 2010, "relativo", 1),
        ("b", 2011, "absoluto", 1),
        ("c", 2011, "absoluto", 0),
    ):
        sumario = f"O prazo é {pos}. Texto integral reservado."
        conn.execute(
            "INSERT INTO acordao(doc_id, processo, url, data_iso, descritores_json, sumario, texto)"
            " VALUES (?,?,?,?,?,?,?)",
            (doc_id, f"{doc_id}/10", URL.format(doc_id), f"{year}-03-01", DESC, sumario, "SECRET"),
        )
        conn.execute(
            "INSERT INTO classification(doc_id, question_id, relevant, position_id, quote,"
            " quote_ok, text_source, prompt_version) VALUES (?,?,?,?,?,?,?,?)",
            (
                doc_id,
                "q6",
                ok,
                pos if ok else None,
                f"O prazo é {pos}",
                ok,
                "sumario",
                "classify_v1",
            ),
        )
    pair = [
        {
            "doc_id": "a",
            "date": "2010-03-01",
            "position": "relativo",
            "quote": "O prazo é relativo",
            "url": URL.format("a"),
        },
        {
            "doc_id": "b",
            "date": "2011-03-01",
            "position": "absoluto",
            "quote": "O prazo é absoluto",
            "url": URL.format("b"),
        },
    ]
    ev = {"support": {"relativo": 2, "absoluto": 2}, "pair": pair, "resolves": None}
    rows = [
        ("q6", "split", 2009, 2012, json.dumps(ev), json.dumps(VERDICT), "media"),
        ("q6", "shift", 2009, 2013, json.dumps(ev), None, None),
        (
            "q6",
            "resolved",
            2009,
            2014,
            json.dumps({**ev, "resolves": ["split", 2009, 2012]}),
            None,
            None,
        ),
    ]
    conn.executemany(
        "INSERT INTO divergence(question_id, type, window_start, window_end, evidence_json,"
        " judge_json, rule_confidence) VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    return conn


def test_export_publishes_grounded_positions_and_confirmed_divergences_only(tmp_path):
    conn = make_db(tmp_path)
    out = tmp_path / "data"
    meta = export(conn, TAX, out, auj=NO_AUJ)
    judgments = json.loads((out / "judgments.json").read_text(encoding="utf-8"))
    assert [j["doc_id"] for j in judgments] == ["a", "b"]
    divs = json.loads((out / "divergences.json").read_text(encoding="utf-8"))
    assert [(d["type"], d["display"]) for d in divs] == [
        ("split", "mudanca"),
        ("resolved", "uniformizada"),
    ]
    assert (meta.divergences_shown, meta.divergences_unjudged) == (2, 1)
    published = "".join(p.read_text(encoding="utf-8") for p in out.glob("*.json"))
    assert "SECRET" not in published and "Texto integral reservado" not in published
    assert check(out, tmp_path / "t.db") == []


def test_export_is_deterministic_and_valid_when_empty(tmp_path):
    conn = connect(tmp_path / "t.db")
    a, b = tmp_path / "a", tmp_path / "b"
    export(conn, TAX, a, auj=NO_AUJ)
    export(conn, TAX, b, auj=NO_AUJ)
    for name in ("meta.json", "questions.json", "judgments.json", "divergences.json"):
        assert (a / name).read_text(encoding="utf-8") == (b / name).read_text(encoding="utf-8")
    assert check(a) == []
    questions = json.loads((a / "questions.json").read_text(encoding="utf-8"))
    assert [q["id"] for q in questions] == ["q2", "q3", "q6", "q7", "q8", "q9", "q10"]


def test_check_catches_long_quotes_bad_links_and_ungrounded_quotes(tmp_path):
    conn = make_db(tmp_path)
    out = tmp_path / "data"
    export(conn, TAX, out, auj=NO_AUJ)
    path = out / "judgments.json"
    judgments = json.loads(path.read_text(encoding="utf-8"))
    judgments[0]["url"] = "https://example.com/x"
    judgments[1]["quote"] = "O prazo é inventado"
    path.write_text(json.dumps(judgments), encoding="utf-8")
    errors = check(out, tmp_path / "t.db")
    assert any("dgsi.pt" in e for e in errors) and any("not grounded" in e for e in errors)
    judgments[1]["quote"] = "x" * 401
    path.write_text(json.dumps(judgments), encoding="utf-8")
    assert any("judgments.json" in e for e in check(out))
