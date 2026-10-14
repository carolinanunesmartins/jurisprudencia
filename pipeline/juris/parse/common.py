"""Shared helpers for the dgsi.pt parsers. Pages are windows-1252 (confirmed on saved fixtures)."""

import re
import unicodedata
from datetime import datetime

from selectolax.lexbor import LexborHTMLParser, LexborNode

ENCODING = "cp1252"
_WS = re.compile(r"\s+")
_FILE_RESIDUE = re.compile(r"file:///\S*")
_BLOCK_TAGS = frozenset({"br", "p", "div", "tr", "li"})


class ParseError(ValueError):
    """The page does not have the structure the parser expects."""


def parse_html(raw: bytes) -> LexborHTMLParser:
    return LexborHTMLParser(raw.decode(ENCODING, errors="replace"))


def cell_text(node: LexborNode) -> str:
    """Text of a cell with one line per <br>/<p>, whitespace normalised, residues removed."""
    parts: list[str] = []
    for n in node.traverse(include_text=True):
        if n.tag == "-text":
            parts.append(n.text_content or "")
        elif n.tag in _BLOCK_TAGS:
            parts.append("\n")
    lines = (_WS.sub(" ", line).strip() for line in "".join(parts).split("\n"))
    text = "\n".join(line for line in lines if line)
    return _FILE_RESIDUE.sub("", text).strip()


def label_key(label: str) -> str:
    """'Nº Convencional:' -> 'noconvencional' (ascii, lowercase, alphanumerics only)."""
    folded = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", folded.lower())


def us_date_to_iso(value: str) -> str:
    """dgsi.pt dates are mm/dd/yyyy (SPEC §3)."""
    try:
        return datetime.strptime(value.strip(), "%m/%d/%Y").date().isoformat()
    except ValueError as exc:
        raise ParseError(f"bad date: {value!r}") from exc
