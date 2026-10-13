"""Parser for a single STJ judgment page (SPEC §4 parsing rules, ROADMAP T2.2 groundwork).

The page is a key/value table: a label cell (bgcolor #71B2CF) followed by a value cell.
Footnotes stay inline in `texto`; `file:///` residues and spacer images are dropped.
"""

import hashlib
import json
from dataclasses import asdict, dataclass

from juris.parse.common import ParseError, cell_text, label_key, parse_html, us_date_to_iso

_LABEL_BG = "#71B2CF"

_FIELDS = {
    "processo": "processo",
    "noconvencional": "secao",
    "relator": "relator",
    "descritores": "descritores",
    "datadoacordao": "data",
    "votacao": "votacao",
    "textointegral": "texto_integral",
    "privacidade": "privacidade",
    "meioprocessual": "meio_processual",
    "decisao": "decisao",
    "indicacoeseventuais": "indicacoes_eventuais",
    "sumario": "sumario",
    "decisaotextointegral": "texto",
}


@dataclass(frozen=True)
class ParsedDocument:
    processo: str
    secao: str
    relator: str
    descritores: tuple[str, ...]
    data_iso: str
    votacao: str
    meio_processual: str
    decisao: str
    indicacoes_eventuais: str
    sumario: str
    texto: str

    @property
    def texto_sha256(self) -> str:
        return hashlib.sha256(self.texto.encode("utf-8")).hexdigest()

    def summary_json(self) -> str:
        """Compact, text-free view used by golden tests."""
        d = asdict(self)
        d["texto"] = {"len": len(self.texto), "sha256": self.texto_sha256}
        d["sumario"] = {"len": len(self.sumario), "head": self.sumario[:80]}
        return json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True)


def parse_document(raw: bytes) -> ParsedDocument:
    tree = parse_html(raw)
    found: dict[str, str] = {}
    for tr in tree.css("tr"):
        cells = list(tr.iter(include_text=False))
        if len(cells) != 2 or cells[0].attributes.get("bgcolor") != _LABEL_BG:
            continue
        field = _FIELDS.get(label_key(cell_text(cells[0])))
        if field and field not in found:
            found[field] = cell_text(cells[1])
    if not found.get("processo"):
        raise ParseError("missing 'Processo' field")
    if not found.get("data"):
        raise ParseError("missing 'Data do Acordão' field")
    return ParsedDocument(
        processo=found["processo"],
        secao=found.get("secao", ""),
        relator=found.get("relator", ""),
        descritores=tuple(found["descritores"].split("\n")) if found.get("descritores") else (),
        data_iso=us_date_to_iso(found["data"]),
        votacao=found.get("votacao", ""),
        meio_processual=found.get("meio_processual", ""),
        decisao=found.get("decisao", ""),
        indicacoes_eventuais=found.get("indicacoes_eventuais", ""),
        sumario=found.get("sumario", ""),
        texto=found.get("texto", ""),
    )
