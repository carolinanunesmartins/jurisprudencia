import json
import sqlite3
from pathlib import Path

import httpx
import pytest

from juris.classify.run import build_input, labels_filled, run
from juris.classify.schema import SchemaError, validate_answer
from juris.db.schema import connect
from juris.llm.prompt import CLASSIFY, classify_prompt
from juris.llm.provider import AnthropicProvider, ApiError, ReplayProvider, request_key
from juris.taxonomy.model import load_taxonomy

pytestmark = pytest.mark.unit

TAX = load_taxonomy(Path(__file__).resolve().parents[3] / "data" / "taxonomy.json")
APPROVED = [q.id for q in TAX.questions if q.status == "approved"]
SUMARIO = "I - O sinal só se perde com incumprimento definitivo, não com a simples mora."
DESC = json.dumps(["CONTRATO-PROMESSA", "SINAL"])


def answer(**overrides):
    qs = [{"question_id": q, "relevant": False, "position_id": None, "quote": ""} for q in APPROVED]
    for q, value in overrides.items():
        qs[APPROVED.index(q)] = {"question_id": q, **value}
    return {"questions": qs}


def q3(quote):
    return {"q3": {"relevant": True, "position_id": "exige_definitivo", "quote": quote}}


def make_db(tmp_path, rows):
    conn = connect(tmp_path / "t.db")
    for doc_id, sumario, texto in rows:
        conn.execute(
            "INSERT INTO acordao(doc_id, processo, url, data_iso, descritores_json, sumario, texto,"
            " fetched_at) VALUES (?,?,?,?,?,?,?,?)",
            (doc_id, "1/05", "u", "2010-01-01", DESC, sumario, texto, "x"),
        )
    conn.commit()
    return conn


def record(fixtures: Path, conn, doc_id, value):
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM acordao WHERE doc_id = ?", (doc_id,)).fetchone()
    key = request_key(CLASSIFY, classify_prompt(TAX), build_input(row)[0])
    fixtures.mkdir(exist_ok=True)
    (fixtures / f"{key}.json").write_text(json.dumps({"answer": value}), encoding="utf-8")


def test_schema_accepts_one_answer_per_approved_question():
    got = validate_answer(answer(**q3("x")), TAX)
    assert set(got) == set(APPROVED) and got["q3"].position_id == "exige_definitivo"


@pytest.mark.parametrize(
    "bad",
    [
        {"questions": []},
        answer(q3={"relevant": True, "position_id": "inventada", "quote": "x"}),
        answer(q3={"relevant": True, "position_id": None, "quote": "x"}),
        {"questions": answer()["questions"] + [{"question_id": "q1", "relevant": False}]},
    ],
)
def test_schema_rejects_missing_unknown_or_inconsistent_answers(bad):
    with pytest.raises(SchemaError):
        validate_answer(bad, TAX)


def test_run_stores_grounded_positions_and_rejects_invented_quotes(tmp_path):
    conn = make_db(tmp_path, [("a", SUMARIO, "texto"), ("b", SUMARIO + " II.", "texto")])
    fx = tmp_path / "fx"
    record(fx, conn, "a", answer(**q3("só se perde com incumprimento definitivo")))
    record(fx, conn, "b", answer(**q3("frase que não está no sumário")))
    stats = run(conn, ReplayProvider(fx), TAX)
    assert (stats.judgments, stats.quotes_accepted, stats.quotes_rejected) == (2, 1, 1)
    rows = dict(
        ((d, (r, p, ok, s)))
        for d, r, p, ok, s in conn.execute(
            "SELECT doc_id, relevant, position_id, quote_ok, text_source FROM classification"
            " WHERE question_id = 'q3'"
        )
    )
    assert rows["a"] == (1, "exige_definitivo", 1, "sumario")
    assert rows["b"] == (0, None, 0, "sumario")


def test_run_uses_the_full_text_only_without_a_sumario_and_resumes(tmp_path):
    conn = make_db(tmp_path, [("a", "", "Texto: " + SUMARIO), ("b", SUMARIO, "")])
    fx = tmp_path / "fx"
    record(fx, conn, "a", answer(**q3("com a simples mora")))
    first = run(conn, ReplayProvider(fx), TAX)
    assert (first.judgments, first.missing_fixtures, dict(first.by_source)) == (1, 1, {"texto": 1})
    record(fx, conn, "b", answer())
    second = run(conn, ReplayProvider(fx), TAX)
    assert second.judgments == 1  # "a" is not classified again


def test_schema_failure_is_retried_once_then_counted(tmp_path):
    conn = make_db(tmp_path, [("a", SUMARIO, "")])
    fx = tmp_path / "fx"
    record(fx, conn, "a", {"questions": "not a list"})
    stats = run(conn, ReplayProvider(fx), TAX)
    assert stats.schema_failures == 1 and stats.judgments == 0


def test_anthropic_provider_sends_temperature_0_and_records_a_replay_fixture(tmp_path):
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent.update(json.loads(request.content))
        text = "```json\n" + json.dumps(answer()) + "\n```"
        return httpx.Response(
            200,
            json={"content": [{"type": "text", "text": text}], "usage": {"input_tokens": 7}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    p = AnthropicProvider("k", "m", record=tmp_path, client=client)
    assert p.generate_json("classify_v1", "sys", "in") == answer()
    assert sent["temperature"] == 0 and sent["model"] == "m" and p.usage == {"input_tokens": 7}
    assert ReplayProvider(tmp_path).generate_json("classify_v1", "sys", "in") == answer()


def test_labels_filled_counts_the_blind_sheet(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("n,question,label\n1,q2,basta_mora\n2,q3,\n", encoding="utf-8-sig")
    assert labels_filled(path) == (1, 2)
    assert labels_filled(tmp_path / "none.csv") == (0, 0)


def test_truncated_answer_is_not_retried(tmp_path):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        body = {
            "content": [{"type": "text", "text": "{"}],
            "stop_reason": "max_tokens",
            "usage": {"input_tokens": 10, "output_tokens": 1200},
        }
        return httpx.Response(200, json=body)

    conn = make_db(tmp_path, [("a", SUMARIO, "")])
    client = httpx.Client(transport=httpx.MockTransport(handler))
    stats = run(conn, AnthropicProvider("k", "m", client=client), TAX)
    assert (len(calls), stats.truncated, stats.judgments) == (1, 1, 0)


def test_run_stops_at_the_token_budget(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        body = {
            "content": [{"type": "text", "text": json.dumps(answer())}],
            "usage": {"input_tokens": 600, "output_tokens": 400},
        }
        return httpx.Response(200, json=body)

    conn = make_db(tmp_path, [(c, SUMARIO, "") for c in "abcde"])
    client = httpx.Client(transport=httpx.MockTransport(handler))
    stats = run(conn, AnthropicProvider("k", "m", client=client), TAX, budget_tokens=2000)
    assert stats.judgments == 2 and stats.stopped_by_budget
    rest = run(conn, AnthropicProvider("k", "m", client=client), TAX)
    assert rest.judgments == 3  # resumes with the remaining judgments


def test_api_error_shows_the_api_message_not_only_the_status():
    def handler(request):
        body = {"type": "error", "error": {"type": "invalid_request_error", "message": "bad model"}}
        return httpx.Response(400, json=body)

    p = AnthropicProvider("k", "m", client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(ApiError, match="400: invalid_request_error: bad model") as e:
        p.generate_json(CLASSIFY, "s", "i")
    assert e.value.status == 400
