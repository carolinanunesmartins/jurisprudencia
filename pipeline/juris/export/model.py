"""Schemas of the published JSON in web/public/data/ (SPEC §8, §10). Mirrored in web/src/data.ts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from juris.classify.grounding import MAX_QUOTE_CHARS

Quote = Field(max_length=MAX_QUOTE_CHARS)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Meta(_Strict):
    taxonomy_version: str
    prompt_version: str
    subset_size: int
    classified: int
    by_source: dict[str, int]
    quotes_rejected: int
    divergences_shown: int
    divergences_hidden: int  # judged as no real opposition (SPEC §6.4)
    divergences_unjudged: int


class PositionOut(_Strict):
    id: str
    label: str
    definition: str


class QuestionOut(_Strict):
    id: str
    title: str
    description: str
    split: Literal["dev", "test"]
    positions: list[PositionOut]
    counts: dict[str, int]
    first_year: int | None
    last_year: int | None


class JudgmentOut(_Strict):
    doc_id: str
    processo: str
    date: str
    url: str
    secao: str
    relator: str
    question_id: str
    position: str
    quote: str = Quote
    text_source: Literal["sumario", "texto"]
    uniformizacao: bool


class PairItem(_Strict):
    doc_id: str
    processo: str
    date: str
    url: str
    position: str
    quote: str = Quote


class JudgeOut(_Strict):
    real_opposition: bool
    legislative_change_possible: bool
    rationale: str
    confidence: Literal["alta", "media", "baixa"]


class DivergenceOut(_Strict):
    id: str
    question_id: str
    type: Literal["split", "shift", "resolved"]
    window_start: int
    window_end: int
    display: Literal["mudanca", "possivel_alteracao_legislativa", "uniformizada"]
    rule_confidence: Literal["alta", "media", "baixa"] | None
    support: dict[str, int]
    pair: list[PairItem]
    judge: JudgeOut | None


class AujJudgmentOut(_Strict):
    doc_id: str
    processo: str
    date: str
    url: str
    quote: str = Quote  # from the judgment's own sumário


class AujSideOut(_Strict):
    auj_quote: str = Quote  # how the AUJ itself describes this side
    judgments: list[AujJudgmentOut]


class AujOut(_Strict):
    """A divergence documented by the STJ itself: an acórdão de uniformização (SPEC §6.6)."""

    id: str
    doc_id: str
    processo: str
    date: str
    url: str
    related_questions: list[str]
    question_quote: str | None = Field(default=None, max_length=MAX_QUOTE_CHARS)
    conflict_quote: str = Quote
    sides: list[AujSideOut]
    ruling_quote: str = Quote


class ScoreOut(_Strict):
    set: Literal["test", "dev"]
    system: Literal["model", "baseline"]
    rows: int
    unclear: int
    exact: tuple[int, int]
    recall: tuple[int, int]  # label has a position -> same position
    precision: tuple[int, int]  # system gives a position -> label agrees


class CostOut(_Strict):
    input_tokens: int
    output_tokens: int
    usd_estimate: float  # at assumed list prices (data/eval/runs.json)


class SurveyOut(_Strict):
    seed: int
    topic: str
    question: str | None
    result: str


class EvaluationOut(_Strict):
    """Key numbers of data/eval/report.md for /metodo (written by `make evaluate`)."""

    cost: CostOut
    grounding: dict[str, int]
    position: list[ScoreOut]
    divergences: dict[str, int]
    aujs: int
    divergence_labels: dict[str, int] | None
    survey: list[SurveyOut]
