"""Parser for the 'Lista de Descritores' page (`jstj.nsf/desc?OpenPage`), used in ROADMAP T1.3."""

from dataclasses import dataclass

from juris.parse.common import ParseError, cell_text, parse_html

_LEGEND = "Descritor com dupla grafia"


@dataclass(frozen=True)
class Descritor:
    letter: str
    term: str
    variants: tuple[str, ...]  # dual spellings ("A / B *"); equals (term,) otherwise


def parse_descritores(raw: bytes) -> list[Descritor]:
    letter = ""
    out: list[Descritor] = []
    for font in parse_html(raw).css("p font"):
        text = cell_text(font)
        if not text or text == _LEGEND:
            continue
        parent = font.parent
        if parent is not None and parent.tag == "b":
            if len(text) == 1 and text.isalpha():
                letter = text
            continue
        dual = text.endswith("*")
        term = text.rstrip("*").strip()
        variants = tuple(v.strip() for v in term.split(" / ")) if dual else (term,)
        out.append(Descritor(letter=letter, term=term, variants=variants))
    if not out:
        raise ParseError("no descriptors found")
    return out
