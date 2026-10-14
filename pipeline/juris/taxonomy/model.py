"""Taxonomy of legal questions (SPEC §5.1): loaded and validated from data/taxonomy.json."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

Status = Literal["seed", "proposed", "approved", "rejected"]
DEFAULT_PATH = Path("data/taxonomy.json")


class Position(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    label_pt: str
    definition_pt: str


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title_pt: str
    description_pt: str
    norms: list[str]
    positions: list[Position]
    seed_source: str
    status: Status

    @model_validator(mode="after")
    def _positions(self) -> "Question":
        ids = [p.id for p in self.positions]
        if not 2 <= len(ids) <= 3:
            raise ValueError(f"{self.id}: 2-3 positions required")
        if len(set(ids)) != len(ids) or "nao_decide" in ids:
            raise ValueError(f"{self.id}: position ids must be unique and not 'nao_decide'")
        return self


class Taxonomy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str
    questions: list[Question]

    @model_validator(mode="after")
    def _unique(self) -> "Taxonomy":
        ids = [q.id for q in self.questions]
        if len(set(ids)) != len(ids):
            raise ValueError("question ids must be unique")
        return self


def load_taxonomy(path: Path = DEFAULT_PATH) -> Taxonomy:
    return Taxonomy.model_validate(json.loads(path.read_text(encoding="utf-8")))
