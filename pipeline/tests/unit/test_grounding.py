import pytest

from juris.classify.grounding import MAX_QUOTE_CHARS, is_grounded

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
