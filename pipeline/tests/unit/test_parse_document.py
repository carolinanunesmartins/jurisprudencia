from pathlib import Path

import pytest

from juris.parse.common import ParseError
from juris.parse.descritores import parse_descritores
from juris.parse.document import parse_document

pytestmark = pytest.mark.unit

FIX = Path(__file__).parent.parent / "fixtures"
DOCS = ["doc_1.html", "doc_2.html", "doc_3.html", "doc_2000.html"]


def load(name):
    return parse_document((FIX / name).read_bytes())


@pytest.mark.parametrize("name", DOCS)
def test_every_fixture_has_core_fields_and_nonempty_sumario_and_texto(name):
    d = load(name)
    assert d.processo and d.secao.endswith("SECÇÃO") and d.relator
    assert d.descritores and d.sumario and d.texto
    assert d.data_iso.count("-") == 2


@pytest.mark.parametrize("name", DOCS)
def test_no_residues_or_mojibake_in_text(name):
    d = load(name)
    for text in (d.sumario, d.texto):
        assert "file:///" not in text
        assert "�" not in text


def test_fields_of_a_civil_judgment():
    d = load("doc_1.html")
    assert d.processo == "5306/20.0T8BRG.G3.S1"
    assert d.secao == "2.ª SECÇÃO"
    assert d.data_iso == "2026-10-01"
    assert d.meio_processual == "REVISTA"
    assert d.decisao == "NEGADA"
    assert len(d.descritores) == 15


def test_optional_field_indicacoes_eventuais():
    assert load("doc_2000.html").indicacoes_eventuais == "TRANSITADO EM JULGADO"
    assert load("doc_1.html").indicacoes_eventuais == ""


def test_paragraphs_become_lines_and_footnotes_stay_inline():
    d = load("doc_1.html")
    assert "\n" in d.texto
    assert "capacidade judiciária" in d.texto


def test_texto_hash_is_stable_and_hex():
    d = load("doc_2.html")
    assert d.texto_sha256 == load("doc_2.html").texto_sha256
    assert len(d.texto_sha256) == 64


def test_page_without_key_fields_is_a_parse_error():
    with pytest.raises(ParseError):
        parse_document(b"<html><body><table><tr><td>x</td></tr></table></body></html>")


def test_descriptor_list():
    items = parse_descritores((FIX / "descritores.html").read_bytes())
    terms = {i.term for i in items}
    assert len(items) > 4000
    assert {"Abalroação", "Sinal", "Voto do Presidente da Secção"} <= terms
    assert items[0].letter == "A" and items[-1].letter == "V"


def test_dual_spelling_descriptors_expose_both_variants():
    items = parse_descritores((FIX / "descritores.html").read_bytes())
    dual = next(i for i in items if i.term.startswith("Acção cambiária"))
    assert dual.variants == ("Acção cambiária", "Ação cambiária")


def test_processo_ignores_the_link_to_the_relacao_judgment():
    page = (
        "<html><body><table>"
        '<tr><td bgcolor="#71B2CF"><b>Processo:</b></td><td><table><tr>'
        "<td><b><font>04S4759</font></b></td>"
        '<td><a href="/jtrl.nsf/0/X">ver acórdão T REL </a></td></tr></table></td></tr>'
        '<tr><td bgcolor="#71B2CF"><b>Data do Acordão:</b></td><td>07/04/2005</td></tr>'
        "</table></body></html>"
    )
    assert parse_document(page.encode("utf-8")).processo == "04S4759"
