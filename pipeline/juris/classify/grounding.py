"""Quote grounding (AGENTS.md rule 4): a quote is valid only if it is a verbatim
substring of the stored text after whitespace normalisation."""

import re

MAX_QUOTE_CHARS = 400
_WS = re.compile(r"\s+")


def normalise(text: str) -> str:
    return _WS.sub(" ", text).strip()


def is_grounded(quote: str, text: str) -> bool:
    q = normalise(quote)
    if not q or len(q) > MAX_QUOTE_CHARS:
        return False
    return q in normalise(text)
