import json
from pathlib import Path

import pytest

from juris.db.schema import connect
from juris.detect.__main__ import run
from juris.detect.core import Config, Point, detect, is_uniformizacao, load_config, shifts, splits

pytestmark = pytest.mark.unit

CFG = Config()


def pts(spec: str, uniformizacao: set[int] = frozenset()) -> list[Point]:
    """'2005:A 2006:B' -> points; same-year entries get distinct ids and days."""
    out = []
    for i, item in enumerate(spec.split()):
        year, pos = item.split(":")
        out.append(
            Point(f"d{i}", f"{year}-01-{i % 28 + 1:02d}", pos, uniformizacao=i in uniformizacao)
        )
    return out


def test_default_config_matches_detect_toml():
    root = Path(__file__).resolve().parents[3]
    assert load_config(root / "detect.toml") == CFG


def test_settled_question_has_no_divergence():
    assert detect("q", pts("2001:A 2003:A 2005:A 2008:A 2010:A 2015:A 2020:A"), CFG) == []


def test_thin_minority_is_not_a_split():
    # one B among many A: below k=2 in every window
    assert splits("q", pts("2005:A 2006:A 2006:B 2007:A"), CFG) == []


def test_split_in_overlapping_windows_is_one_divergence():
    found = splits("q", pts("2010:A 2010:B 2011:A 2011:B"), CFG)
    assert len(found) == 1
    d = found[0]
    assert (d.window_start, d.window_end) == (2009, 2012)
    assert d.support == {"A": 2, "B": 2}
    assert [p.position for p in d.pair] == ["A", "B"]


def test_two_separate_splits_stay_separate():
    found = splits("q", pts("2002:A 2002:B 2003:A 2003:B 2020:A 2020:B 2021:A 2021:B"), CFG)
    assert [(d.window_start, d.window_end) for d in found] == [(2001, 2004), (2019, 2022)]


def test_shift_needs_disjoint_windows_and_reports_the_opposing_pair():
    found = shifts("q", pts("2001:A 2002:A 2003:A 2010:B 2011:B 2012:B"), CFG)
    assert len(found) == 1
    d = found[0]
    assert d.pair[0].year == 2003 and d.pair[1].year == 2010
    assert (d.window_start, d.window_end) == (2002, 2011)
    assert d.support == {"A": 2, "B": 2}  # support inside the two windows compared


def test_dominance_below_threshold_is_no_shift():
    # 2 A vs 2 B in the later period: no dominant position there
    assert shifts("q", pts("2001:A 2002:A 2003:A 2010:A 2010:B 2011:A 2011:B"), CFG) == []


def test_adjacent_periods_count_as_a_shift():
    # A dominates a window ending 2006, B one starting 2007: a shift under SPEC §6.2
    found = shifts("q", pts("2005:A 2005:A 2007:B 2007:B 2007:B"), CFG)
    assert [(d.pair[0].year, d.pair[1].year) for d in found] == [(2005, 2007)]


def test_uniformizacao_after_a_split_resolves_it():
    found = detect("q", pts("2010:A 2010:B 2011:A 2011:B 2014:A", uniformizacao={4}), CFG)
    resolved = [d for d in found if d.type == "resolved"]
    assert len(resolved) == 1 and resolved[0].pair[0].doc_id == "d4"
    assert resolved[0].resolves == ("split", 2009, 2012)


def test_uniformizacao_before_the_divergence_does_not_resolve_it():
    found = detect("q", pts("2001:A 2010:A 2010:B 2011:A 2011:B", uniformizacao={0}), CFG)
    assert [d.type for d in found] == ["split"]


def test_uniformizacao_marker_is_accent_and_case_insensitive():
    assert is_uniformizacao("Recurso para Uniformização de Jurisprudência", "")
    assert is_uniformizacao("Revista", "x" * 100 + "UNIFORMIZACAO DE JURISPRUDENCIA")


def test_uniformizacao_marker_survives_the_source_typo_in_meio_processual():
    # regression: AUJ 4/2014 is listed as "UNIFORMIZAÇÃO DE JURSIPRUDÊNCIA" on dgsi.pt
    assert is_uniformizacao("UNIFORMIZAÇÃO DE JURSIPRUDÊNCIA", "")
    assert not is_uniformizacao("REVISTA", "cita o acórdão uniformizador n.º 4/2014")
    assert not is_uniformizacao("Revista", "x" * 2000 + "uniformização de jurisprudência")


def test_detect_main_reads_grounded_classifications_only(tmp_path, capsys):
    root = Path(__file__).resolve().parents[3]
    conn = connect(tmp_path / "t.db")
    data = [
        ("a", 2010, "relativo", 1),
        ("b", 2010, "absoluto", 1),
        ("c", 2011, "relativo", 1),
        ("d", 2011, "absoluto", 1),
        ("e", 2011, "absoluto", 0),
    ]
    for doc_id, year, pos, ok in data:
        conn.execute(
            "INSERT INTO acordao(doc_id, processo, url, data_iso) VALUES (?,?,?,?)",
            (doc_id, "p", f"u/{doc_id}", f"{year}-02-01"),
        )
        conn.execute(
            "INSERT INTO classification(doc_id, question_id, relevant, position_id, quote,"
            " quote_ok, prompt_version) VALUES (?,?,?,?,?,?,?)",
            (doc_id, "q6", ok, pos if ok else None, "x", ok, "classify_v1"),
        )
    found = run(conn, root / "data" / "taxonomy.json", root / "detect.toml")
    assert [d.type for d in found] == ["split"]
    (evidence,) = conn.execute("SELECT evidence_json FROM divergence").fetchone()
    assert json.loads(evidence)["support"] == {"absoluto": 2, "relativo": 2}
    assert "q6 [test]" in capsys.readouterr().out


V2 = Config(
    window_years=3, min_support=2, dominance=0.6, first_year=2000, last_year=2025, pair_rule="v2"
)


def P(doc, date, pos, partial=False):
    return Point(doc, date, pos, partial=partial)


def test_pair_rule_v2_split_takes_the_closest_whole_quotes():
    points = [
        P("a1", "2010-01-01", "A"),
        P("b1", "2010-01-05", "B", partial=True),  # v1 would show this one
        P("a2", "2010-06-01", "A"),
        P("b2", "2010-06-10", "B"),
        P("a3", "2011-01-01", "A"),
        P("b3", "2011-03-01", "B"),
    ]
    (v1,) = splits("q", points, CFG)
    (v2,) = splits("q", points, V2)
    assert [p.doc_id for p in v1.pair] == ["a1", "b1"]
    assert [p.doc_id for p in v2.pair] == ["a2", "b2"]


def test_pair_rule_v2_falls_back_when_a_side_has_only_partial_quotes():
    points = [
        P("a1", "2010-01-01", "A"),
        P("b1", "2010-02-01", "B", partial=True),
        P("a2", "2011-01-01", "A"),
        P("b2", "2011-02-01", "B", partial=True),
    ]
    assert splits("q", points, V2)[0].pair == splits("q", points, CFG)[0].pair


def test_pair_rule_v2_shift_skips_a_partial_quote():
    points = [P(f"a{i}", f"200{i}-01-01", "A") for i in range(3)]
    points += [P("a3", "2002-06-01", "A", partial=True)]
    points += [P(f"b{i}", f"20{10 + i}-01-01", "B") for i in range(3)]
    (shift,) = [d for d in detect("q", points, V2) if d.type == "shift"]
    assert shift.pair[0].doc_id == "a2"


def test_partial_flag_is_not_part_of_the_evidence():
    d = splits(
        "q",
        [
            P("a", "2010-01-01", "A", True),
            P("b", "2010-02-01", "B"),
            P("c", "2010-03-01", "A"),
            P("e", "2010-04-01", "B"),
        ],
        CFG,
    )[0]
    assert all("partial" not in p for p in d.evidence()["pair"])
