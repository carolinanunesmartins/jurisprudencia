import json
from pathlib import Path

import pytest

from juris.db.schema import connect
from juris.db.snapshot import dump, load
from juris.detect.__main__ import run as detect_run
from juris.export.__main__ import export
from tests.unit.test_export import DESC, TAX, URL, VERDICT, make_db

pytestmark = pytest.mark.unit

NO_AUJ = Path("no-such-auj.json")  # the real AUJ cards refer to judgments not in test DBs

CFG = TAX.parents[1] / "detect.toml"


def test_snapshot_has_no_texts_and_withholds_rejected_quotes(tmp_path):
    dump(make_db(tmp_path), tmp_path / "snap", auj=NO_AUJ)
    raw = "".join(p.read_text(encoding="utf-8") for p in (tmp_path / "snap").iterdir())
    assert "SECRET" not in raw and "Texto integral reservado" not in raw
    rows = [
        json.loads(line)
        for line in (tmp_path / "snap" / "classification.jsonl").open(encoding="utf-8")
    ]
    assert {r["doc_id"]: r["quote"] for r in rows} == {
        "a": "O prazo é relativo",
        "b": "O prazo é absoluto",
        "c": None,
    }


def test_a_database_rebuilt_from_the_snapshot_exports_the_same_site_data(tmp_path):
    conn = make_db(tmp_path)
    export(conn, TAX, tmp_path / "orig", auj=NO_AUJ)
    dump(conn, tmp_path / "snap", auj=NO_AUJ)
    load(tmp_path / "fresh.db", tmp_path / "snap")
    export(connect(tmp_path / "fresh.db"), TAX, tmp_path / "again", auj=NO_AUJ)
    for f in (tmp_path / "orig").iterdir():
        assert (tmp_path / "again" / f.name).read_text(encoding="utf-8") == f.read_text(
            encoding="utf-8"
        ), f.name


def test_load_refuses_to_overwrite_a_database(tmp_path):
    (tmp_path / "x.db").write_bytes(b"")
    with pytest.raises(FileExistsError):
        load(tmp_path / "x.db", tmp_path)


def _split_db(tmp_path):
    conn = connect(tmp_path / "d.db")
    for i, (year, pos) in enumerate([(2010, "relativo"), (2010, "absoluto")] * 2):
        doc = f"d{i}"
        conn.execute(
            "INSERT INTO acordao(doc_id, processo, url, data_iso, descritores_json, texto)"
            " VALUES (?,?,?,?,?,?)",
            (doc, doc, URL.format(doc), f"{year}-0{i + 1}-01", DESC, ""),
        )
        conn.execute(
            "INSERT INTO classification(doc_id, question_id, relevant, position_id, quote,"
            " quote_ok, prompt_version) VALUES (?,?,1,?,?,1,'classify_v1')",
            (doc, "q6", pos, f"citação {i}"),
        )
    conn.commit()
    return conn


def test_detect_keeps_a_verdict_while_the_evidence_is_unchanged(tmp_path, capsys):
    conn = _split_db(tmp_path)
    assert detect_run(conn, TAX, CFG)
    conn.execute(
        "UPDATE divergence SET judge_json = ?, rule_confidence = 'media'", (json.dumps(VERDICT),)
    )
    detect_run(conn, TAX, CFG)
    assert conn.execute("SELECT COUNT(*) FROM divergence WHERE judge_json IS NULL").fetchone() == (
        0,
    )
    conn.execute("UPDATE classification SET quote = 'outra citação'")  # the judge saw other quotes
    detect_run(conn, TAX, CFG)
    assert conn.execute(
        "SELECT COUNT(*) FROM divergence WHERE judge_json IS NOT NULL"
    ).fetchone() == (0,)
