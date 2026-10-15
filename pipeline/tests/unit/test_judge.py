import json
from pathlib import Path

import pytest

from juris.db.schema import connect
from juris.detect import judge
from juris.llm.provider import MissingFixture, ReplayProvider, request_key
from juris.taxonomy.model import load_taxonomy

pytestmark = pytest.mark.unit

TAX = load_taxonomy(Path(__file__).resolve().parents[3] / "data" / "taxonomy.json")
SYSTEM = "judge instructions"


def pair(a="relativo", b="absoluto"):
    return [
        {"doc_id": "x", "date": "2010-01-01", "position": a, "quote": "prazo relativo"},
        {"doc_id": "y", "date": "2012-01-01", "position": b, "quote": "prazo absoluto"},
    ]


def add(conn, qid, kind, support, p):
    ev = {"support": support, "pair": p, "resolves": None}
    conn.execute(
        "INSERT INTO divergence(question_id, type, window_start, window_end, evidence_json)"
        " VALUES (?,?,?,?,?)",
        (qid, kind, 2009, 2012, json.dumps(ev)),
    )


def fixture(dir_, qid, p, verdict):
    key = request_key(judge.JUDGE, SYSTEM, judge.judge_input(TAX, qid, p))
    dir_.mkdir(exist_ok=True)
    (dir_ / f"{key}.json").write_text(json.dumps({"answer": verdict}), encoding="utf-8")


VERDICT = {"real_opposition": True, "legislative_change_possible": False, "confidence": "media"}


@pytest.mark.parametrize(
    "support, agrees, expected",
    [
        ({"relativo": 3, "absoluto": 4}, True, "alta"),
        ({"relativo": 2, "absoluto": 9}, True, "media"),
        ({"relativo": 3, "absoluto": 3}, False, "baixa"),
        ({"relativo": 1, "absoluto": 9}, True, "baixa"),
    ],
)
def test_rule_confidence_follows_spec_6_5(support, agrees, expected):
    assert judge.rule_confidence(support, ["relativo", "absoluto"], agrees) == expected


def test_strength_ranks_balanced_support_first():
    assert judge.strength({"a": 3, "b": 3}, ["a", "b"]) > judge.strength(
        {"a": 9, "b": 2}, ["a", "b"]
    )


def test_display_follows_spec_6_4():
    v = judge.Verdict(**VERDICT)
    assert judge.display(v) == "mudanca"
    assert judge.display(v.model_copy(update={"legislative_change_possible": True})) == (
        "possivel_alteracao_legislativa"
    )
    assert judge.display(v.model_copy(update={"real_opposition": False})) is None


def test_run_stores_verdicts_and_gate_g3_counts_test_questions_only(tmp_path, capsys):
    conn = connect(tmp_path / "t.db")
    conn.execute("INSERT INTO classification(doc_id, question_id, relevant) VALUES ('x','q6',1)")
    add(conn, "q6", "split", {"relativo": 2, "absoluto": 2}, pair())
    add(
        conn,
        "q3",
        "shift",
        {"basta_mora": 2, "exige_definitivo": 3},
        pair("basta_mora", "exige_definitivo"),
    )
    fx = tmp_path / "fx"
    fixture(fx, "q6", pair(), VERDICT)
    fixture(fx, "q3", pair("basta_mora", "exige_definitivo"), VERDICT)
    stats = judge.run(conn, ReplayProvider(fx), TAX, SYSTEM)
    assert stats == {"judged": 2, "not_judged": 0, "invalid": 0}
    confs = dict(conn.execute("SELECT question_id, rule_confidence FROM divergence"))
    assert confs == {"q6": "media", "q3": "media"}
    assert judge.gate_g3(conn) == 1  # q3 is dev
    assert "STAY" in capsys.readouterr().out


def test_cached_provider_uses_the_replay_before_the_live_call(tmp_path):
    class Live:
        model = "m"
        calls = 0

        def generate_json(self, prompt_id, system, input):
            Live.calls += 1
            return {"live": True}

    fixture(tmp_path, "q6", pair(), VERDICT)
    cached = judge.CachedProvider(ReplayProvider(tmp_path), Live())
    assert (
        cached.generate_json(judge.JUDGE, SYSTEM, judge.judge_input(TAX, "q6", pair())) == VERDICT
    )
    assert cached.generate_json(judge.JUDGE, SYSTEM, "other") == {"live": True}
    assert Live.calls == 1
    with pytest.raises(MissingFixture):
        ReplayProvider(tmp_path).generate_json(judge.JUDGE, SYSTEM, "other")
