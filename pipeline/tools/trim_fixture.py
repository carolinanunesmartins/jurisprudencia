"""Trim a saved judgment page so it can be committed (AGENTS.md rule 3: no full texts).

Usage: python pipeline/tools/trim_fixture.py RAW.html OUT.html
Keeps the header table, the first 2 paragraphs of the Sumário, the first 4 paragraphs of the
full text, up to 3 paragraphs with footnote markers (<sup>) or file:/// residues, and the
closing markup. Original bytes elsewhere are untouched (windows-1252).
"""

import re
import sys
from pathlib import Path

ENC = "cp1252"
KEEP_HEAD_SUMARIO = 2
KEEP_HEAD_TEXTO = 4
KEEP_SPECIAL = 3
SPECIAL = re.compile(r"<sup|file:///")


def _trim_cell(chunks: list[str], head: int) -> list[str]:
    keep = set(range(min(head, len(chunks))))
    keep.add(len(chunks) - 1)  # closing markup
    special = [i for i, c in enumerate(chunks) if SPECIAL.search(c) and i not in keep]
    keep.update(special[:KEEP_SPECIAL])
    return [c for i, c in enumerate(chunks) if i in keep]


def trim(html: str) -> str:
    sum_at = html.index("Sumário :")
    texto_at = html.index("Decisão Texto Integral:")
    cell_start = html.index("<p>", texto_at)
    end = html.rindex("</td></tr>")
    texto_chunks = html[cell_start:end].split("<p>")
    new_texto = "<p>".join(_trim_cell(texto_chunks, KEEP_HEAD_TEXTO))

    row_end = html.index("</td></tr>", sum_at)
    s_start = html.index("<p>", sum_at)
    if s_start < row_end:
        s_chunks = html[s_start:row_end].split("<p>")
        new_sum = "<p>".join(_trim_cell(s_chunks, KEEP_HEAD_SUMARIO))
        return html[:s_start] + new_sum + html[row_end:cell_start] + new_texto + html[end:]
    return html[:cell_start] + new_texto + html[end:]


def main() -> int:
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    out = trim(src.read_bytes().decode(ENC))
    dst.write_bytes(out.encode(ENC))
    print(f"{src.name}: {src.stat().st_size} -> {dst.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
