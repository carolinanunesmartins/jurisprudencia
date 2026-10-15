import pytest

from juris.classify.grounding import MAX_QUOTE_CHARS, ground, is_grounded

pytestmark = pytest.mark.unit

TEXT = "O sinal   tem função\n confirmatória.  A mora não basta."


def test_verbatim_quote_with_different_whitespace_is_grounded():
    assert is_grounded("sinal tem função confirmatória", TEXT)


def test_paraphrase_is_rejected():
    assert not is_grounded("o sinal serve para confirmar", TEXT)


def test_empty_quote_is_rejected():
    assert not is_grounded("   ", TEXT)


def test_quote_over_limit_is_rejected():
    long_text = "a" * (MAX_QUOTE_CHARS + 1)
    assert not is_grounded(long_text, long_text)


SUMARIO = (
    "I - O sinal tem função “compulsória” da celebração do contrato. "
    "II – A conversão da mora em incumprimento definitivo realiza-se pela interpelação. "
    "8) Só o incumprimento definitivo dá lugar à restituição do sinal em dobro."
)


def test_ground_returns_the_texts_own_words():
    assert ground("sinal tem   função", SUMARIO) == ("sinal tem função", {"exact"})


def test_ground_accepts_straight_quotes_and_stores_the_curly_ones():
    span, how = ground('função "compulsória" da', SUMARIO)
    assert span == "função “compulsória” da" and how == {"typography"}


def test_ground_accepts_a_dropped_paragraph_number_and_stores_it():
    span, how = ground("do contrato. A conversão da mora", SUMARIO)
    assert span == "do contrato. II – A conversão da mora" and how == {"numbering"}


def test_ground_ellipsis_stores_the_longest_piece_only_if_all_pieces_are_in_order():
    q = "O sinal tem função... Só o incumprimento definitivo dá lugar à restituição"
    span, how = ground(q, SUMARIO)
    assert span == "Só o incumprimento definitivo dá lugar à restituição" and how == {"ellipsis"}
    assert ground("Só o incumprimento definitivo... O sinal tem função", SUMARIO)[0] is None
    assert ground("O sinal tem função... algo que não está no texto", SUMARIO)[0] is None


def test_ground_trims_an_over_long_exact_quote_at_a_sentence_end():
    text = ("Primeira frase curta. " * 30).strip()
    span, how = ground(text, text)
    assert how == {"trimmed"} and len(span) <= MAX_QUOTE_CHARS and span.endswith(".")
    assert is_grounded(span, text)


def test_ground_rejects_a_paraphrase():
    assert ground("o sinal serve para confirmar", SUMARIO) == (None, {"rejected"})


def test_ground_mends_broken_spacing_and_hyphens_but_stores_the_text_as_is():
    text = "O contrato-promes-sa de compra e venda , embora acompanhado de tradição."
    span, how = ground("O contrato-promessa de compra e venda, embora acompanhado", text)
    assert span == "O contrato-promes-sa de compra e venda , embora acompanhado"
    assert how == {"spacing"}


def test_ground_accepts_a_bracketed_ellipsis():
    span, how = ground("O sinal tem função [...] Só o incumprimento definitivo dá lugar", SUMARIO)
    assert span == "Só o incumprimento definitivo dá lugar" and how == {"ellipsis"}


def test_ground_drops_a_final_stop_the_text_does_not_have():
    span, how = ground("A conversão da mora em incumprimento definitivo.", SUMARIO)
    assert span == "A conversão da mora em incumprimento definitivo"
    assert how == {"punctuation"}


def test_ground_still_rejects_a_changed_word():
    assert ground("A conversão da mora em incumprimento absoluto", SUMARIO)[0] is None
