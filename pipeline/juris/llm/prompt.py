"""Versioned prompts (SPEC §6.1): templates in prompts/*.md, rendered from the taxonomy."""

from pathlib import Path

from juris.taxonomy.model import Taxonomy

PROMPTS = Path(__file__).parent / "prompts"
CLASSIFY = "classify_v1"


def render_questions(tax: Taxonomy) -> str:
    """Approved questions only: rejected and proposed ones never reach classification."""
    lines = []
    for q in tax.questions:
        if q.status != "approved":
            continue
        lines.append(f"- **{q.id}** — {q.title_pt}. {q.description_pt}")
        lines += [f"  - `{p.id}`: {p.definition_pt}" for p in q.positions]
    return "\n".join(lines)


def classify_prompt(tax: Taxonomy, prompt_id: str = CLASSIFY) -> str:
    template = (PROMPTS / f"{prompt_id}.md").read_text(encoding="utf-8")
    return template.replace("{{QUESTIONS}}", render_questions(tax))
