"""Parser for the 'Por Ano' index listing of jstj.nsf (SPEC §3, ROADMAP T1.2)."""

from dataclasses import dataclass

from juris.crawl.client import canonical_url
from juris.parse.common import ParseError, cell_text, parse_html, us_date_to_iso


@dataclass(frozen=True)
class IndexRow:
    processo: str
    url: str
    sessao_iso: str
    relator: str
    descritores: tuple[str, ...]

    @property
    def doc_id(self) -> str:
        """Last path segment of `.../<view-id>/<doc_id>?OpenDocument`; unique per judgment."""
        return self.url.split("?")[0].rsplit("/", 1)[-1]


@dataclass(frozen=True)
class IndexPage:
    rows: tuple[IndexRow, ...]
    next_url: str | None


def parse_index(raw: bytes) -> IndexPage:
    """Rows are the 4-cell table rows whose second cell links to an OpenDocument URL.

    Pagination: follow the 'Seguinte' link. `Start` values are Domino view positions and are
    not multiples of the page size, so they must not be computed. Consecutive pages can share
    a row (last row of page N == first row of page N+1): callers must de-duplicate by `processo`.
    """
    tree = parse_html(raw)
    rows: list[IndexRow] = []
    for tr in tree.css("tr"):
        cells = list(tr.iter(include_text=False))
        if len(cells) != 4 or any(c.tag != "td" for c in cells):
            continue
        link = cells[1].css_first("a[href*='OpenDocument']")
        if link is None:
            continue
        rows.append(
            IndexRow(
                processo=cell_text(link),
                url=canonical_url(link.attributes["href"] or ""),
                sessao_iso=us_date_to_iso(cell_text(cells[0])),
                relator=cell_text(cells[2]),
                descritores=tuple(cell_text(cells[3]).split("\n")) if cell_text(cells[3]) else (),
            )
        )
    if not rows:
        raise ParseError("no index rows found")
    next_links = [a for a in tree.css("a") if cell_text(a) == "Seguinte"]
    next_url = next_links[0].attributes["href"] if next_links else None
    return IndexPage(rows=tuple(rows), next_url=next_url)
