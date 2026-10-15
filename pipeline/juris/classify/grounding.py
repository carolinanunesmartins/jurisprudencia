"""Quote grounding (AGENTS.md rule 4): a quote is valid only if it is a verbatim
substring of the stored text after whitespace normalisation.

`ground` locates the model's quote in the text and returns the matched span of the text itself,
so the stored quote is always verbatim even when the model's copy differs in typography, drops a
paragraph number or joins passages with "...". Each repair is named and counted (SPEC §6.1).
"""

import re

MAX_QUOTE_CHARS = 400
_WS = re.compile(r"\s+")
# one character to one character, so indices in the folded text are indices in the text
_FOLD = str.maketrans(dict.fromkeys("“”„«»″‘’‚′'", '"') | dict.fromkeys("–—‑", "-"))
# a paragraph number or bullet the model left out: "II - ", "IV -", "8) ", "V- ", "b) ", "- "
_ENUM = r" (?:(?:[IVXLC]+|\d{1,3}|[a-z])? ?[-.)] ?)?"
# "...", "…", "[...]", "(…)"
_ELLIPSIS = re.compile(r"\s*(?:[\[(](?:\.\.\.|…)[\])]|\.\.\.|…)\s*")
# ignored by the last-resort match: spaces and hyphens, where the source text is often broken
# ("promes-sa", "contratopromessa", "venda ,") and the model silently mends it
_LOOSE_DROP = frozenset(" -")


def normalise(text: str) -> str:
    return _WS.sub(" ", text).strip()


def is_grounded(quote: str, text: str) -> bool:
    q = normalise(quote)
    if not q or len(q) > MAX_QUOTE_CHARS:
        return False
    return q in normalise(text)


def _find(seg: str, text: str, folded: str, start: int) -> tuple[int, int, set[str]] | None:
    i = text.find(seg, start)
    if i >= 0:
        return i, i + len(seg), set()
    fseg = seg.translate(_FOLD)
    i = folded.find(fseg, start)
    if i >= 0:
        return i, i + len(seg), {"typography"}
    pattern = _ENUM.join(re.escape(t) for t in fseg.split(" "))
    m = re.compile(pattern).search(folded, start)
    if m:
        return m.start(), m.end(), {"numbering"}
    hit = _find_loose(fseg, folded, start)
    if hit:
        return hit[0], hit[1], {"spacing"}
    trimmed = seg.rstrip(".,;: ")  # a full stop the model put where the text goes on
    if trimmed and trimmed != seg:
        found = _find(trimmed, text, folded, start)
        if found:
            return found[0], found[1], found[2] | {"punctuation"}
    return None


def _find_loose(fseg: str, folded: str, start: int) -> tuple[int, int] | None:
    """Match ignoring spaces and hyphens; returns the span in the text, ends on real chars."""
    index = [i for i in range(start, len(folded)) if folded[i] not in _LOOSE_DROP]
    loose = "".join(folded[i] for i in index)
    key = "".join(c for c in fseg if c not in _LOOSE_DROP)
    k = loose.find(key) if key else -1
    if k < 0:
        return None
    return index[k], index[k + len(key) - 1] + 1


def _trim(span: str) -> str:
    """Cut an over-long span at its last sentence end within the limit, else at a word."""
    cut = span[:MAX_QUOTE_CHARS]
    end = cut.rfind(". ")
    if end > 0:
        return cut[: end + 1]
    return cut[: cut.rfind(" ")] if " " in cut else cut


def ground(quote: str, text: str) -> tuple[str | None, set[str]]:
    """(verbatim span of `text` to store, repairs applied); (None, {"rejected"}) if not found."""
    q, t = normalise(quote), normalise(text)
    if not q:
        return None, {"rejected"}
    folded = t.translate(_FOLD)
    found = _find(q, t, folded, 0)  # a "..." may be in the text itself
    repairs: set[str] = set()
    if found:
        i, j, repairs = found
    else:
        segments = [s for s in _ELLIPSIS.split(q) if s]
        if not segments or segments == [q]:
            return None, {"rejected"}
        # every piece must be found, in order; only the longest is stored
        pos, spans = 0, []
        for seg in segments:
            hit = _find(seg, t, folded, pos)
            if hit is None:
                return None, {"rejected"}
            spans.append(hit[:2])
            repairs |= hit[2]
            pos = hit[1]
        i, j = max(spans, key=lambda s: s[1] - s[0])
        repairs.add("ellipsis")
    span = t[i:j]
    if len(span) > MAX_QUOTE_CHARS:
        span = _trim(span)
        repairs.add("trimmed")
    if not is_grounded(span, text):  # the hard gate is unchanged
        return None, {"rejected"}
    return span, repairs or {"exact"}
