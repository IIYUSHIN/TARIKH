"""Domain models. Plain pydantic classes, no behaviour beyond validation."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocType(str, Enum):
    CHEQUE = "cheque"
    RETURN_MEMO = "return_memo"
    DEMAND_NOTICE = "demand_notice"


class SourceRef(BaseModel):
    """Where on a document a fact was read. Polygon is x,y pairs scaled 0..1."""
    doc_id: str
    page: int = 1
    polygon: list[float] = Field(default_factory=list)


class Fact(BaseModel):
    id: str
    doc_id: str
    key: str
    label: str
    value: str | None = None
    confidence: float | None = None
    source: SourceRef | None = None
    verified: bool = False
    manual: bool = False  # lawyer must supply (e.g. date the memo was received)


class Observation(BaseModel):
    """What the model saw on the cheque image, separate from extracted fields."""
    key: str
    label: str
    status: Literal["present", "absent", "unclear"]
    note: str = ""


class Document(BaseModel):
    id: str
    matter_id: str
    doc_type: DocType
    filename: str
    path: str
    facts: list[Fact] = Field(default_factory=list)
    observations: list[Observation] = Field(default_factory=list)


class Entity(BaseModel):
    text: str
    category: str


class Transcript(BaseModel):
    language: str
    text: str
    redacted_text: str
    entities: list[Entity] = Field(default_factory=list)
    key_phrases: list[str] = Field(default_factory=list)
    redaction_route: Literal["source-language", "translated-first"] = "source-language"


class Claim(BaseModel):
    text: str
    fact_ids: list[str]


class Brief(BaseModel):
    claims: list[Claim]
    flagged: list[str] = Field(default_factory=list)
    model: str
    drafted_at: datetime = Field(default_factory=utcnow)


class Matter(BaseModel):
    id: str
    title: str
    created_at: datetime = Field(default_factory=utcnow)
    documents: list[Document] = Field(default_factory=list)
    transcript: Transcript | None = None
    brief: Brief | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None


class AuditEntry(BaseModel):
    id: int
    matter_id: str
    ts: datetime
    actor: str
    action: str
    detail: dict = Field(default_factory=dict)


class Redaction(BaseModel):
    redacted_text: str
    entities: list[Entity] = Field(default_factory=list)


class ToolCall(BaseModel):
    name: str
    args: dict
    result: dict


class Answer(BaseModel):
    text: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
