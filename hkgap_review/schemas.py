from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["minor", "major", "show-stopper"]


class Paragraph(BaseModel):
    section: str
    index: int
    text: str


class ChecklistItem(BaseModel):
    item: str
    category: str = "General"


class RefereeItem(BaseModel):
    category: str
    comment: str
    severity: Severity


class AgentReview(BaseModel):
    agent: str
    commentary: str | None = None
    referee_items: list[RefereeItem] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    integrity_flags: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)


class MergedCommentary(BaseModel):
    paragraph: Paragraph
    verbatim: str
    explainer_commentary: str
    referee_critique: list[RefereeItem] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    integrity_flags: list[str] = Field(default_factory=list)
    agent_raw_outputs: dict[str, dict] = Field(default_factory=dict)


class ReviewReport(BaseModel):
    generated_at_utc: datetime
    model_name: str
    executive_summary: str
    paragraphs: list[MergedCommentary] = Field(default_factory=list)
