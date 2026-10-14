import pytest

from juris.db.schema import connect
from juris.db.subset import in_subset, subset_ids, theme_descriptor

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "descriptor",
    [
        "CONTRATO-PROMESSA",
        "CONTRATO-PROMESSA DE COMPRA E VENDA",
        "CONTRATO PROMESSA",
        "CONTRATO - PROMESSA DE COMPRA E VENDA",
        "Contrato-Promessa de Cessão de Quotas",
        "PROMESSA DE COMPRA E VENDA",
        "PROMESSA UNILATERAL",
    ],
)
def test_theme_descriptors_match(descriptor):
    assert theme_descriptor(descriptor)


@pytest.mark.parametrize(
    "descriptor",
    [
        "EXTRADIÇÃO",  # contains TRADICAO
        "CONTRADIÇÃO INSANÁVEL DA FUNDAMENTAÇÃO",  # contains TRADICAO
        "CARÁCTER SINALAGMÁTICO",  # contains SINAL
        "PROMESSA DE CASAMENTO",
        "SEDUÇÃO COM PROMESSA DE CASAMENTO",
        "PROMESSA AO PÚBLICO",
        "SINAL",
        "EXECUÇÃO ESPECÍFICA",
    ],
)
def test_other_descriptors_do_not_match(descriptor):
    assert not theme_descriptor(descriptor)


def test_year_window_is_inclusive_2000_to_2025():
    d = ["CONTRATO-PROMESSA"]
    assert in_subset("2000-01-01", d) and in_subset("2025-12-31", d)
    assert not in_subset("1999-12-31", d) and not in_subset("2026-01-01", d)
    assert not in_subset(None, d)


def test_subset_ids_reads_descriptors_from_the_database(tmp_path):
    conn = connect(tmp_path / "t.db")
    rows = [
        ("a", "2010-05-05", '["SINAL", "CONTRATO-PROMESSA"]'),
        ("b", "2010-05-05", '["EXTRADIÇÃO"]'),
        ("c", "1990-05-05", '["CONTRATO-PROMESSA"]'),
        ("d", "2012-05-05", None),
    ]
    for doc_id, data_iso, dj in rows:
        conn.execute(
            "INSERT INTO acordao(doc_id, processo, url, data_iso, descritores_json)"
            " VALUES (?,?,?,?,?)",
            (doc_id, "p", "u", data_iso, dj),
        )
    assert subset_ids(conn) == {"a"}
