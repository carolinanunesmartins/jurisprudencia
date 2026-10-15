"""Validation of the model's classification answer (SPEC §6.1). LLM output is untrusted (rule 5)."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from juris.taxonomy.model import Taxonomy


class Answer(BaseModel):
    model_config = ConfigDict(extra="ignore")
    question_id: str
    relevant: bool
    position_id: str | None = None
    quote: str = ""
    note: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def _consistent(self) -> "Answer":
        if self.relevant and not self.position_id:
            raise ValueError(f"{self.question_id}: relevant without position_id")
        if not self.relevant:
            self.position_id, self.quote = None, ""
        return self


class Output(BaseModel):
    model_config = ConfigDict(extra="ignore")
    questions: list[Answer]


class SchemaError(ValueError):
    pass


def validate_answer(raw: object, tax: Taxonomy) -> dict[str, Answer]:
    """One Answer per approved question, keyed by id. Raises SchemaError on any mismatch."""
    try:
        out = Output.model_validate(raw)
    except ValidationError as e:
        raise SchemaError(str(e)) from e
    positions = {q.id: {p.id for p in q.positions} for q in tax.questions if q.status == "approved"}
    got: dict[str, Answer] = {}
    for a in out.questions:
        if a.question_id not in positions or a.question_id in got:
            raise SchemaError(f"unexpected or repeated question {a.question_id!r}")
        if a.relevant and a.position_id not in positions[a.question_id]:
            raise SchemaError(f"{a.question_id}: unknown position {a.position_id!r}")
        got[a.question_id] = a
    missing = set(positions) - set(got)
    if missing:
        raise SchemaError(f"missing questions {sorted(missing)}")
    return got
