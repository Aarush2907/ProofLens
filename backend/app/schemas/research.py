import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.services.questions import normalise_question


class ResearchQuestionCreate(BaseModel):
    question: str = Field(max_length=4000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        return normalise_question(value)


class ResearchQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    status: str
    stage: str = "submitted"
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_timestamp(self, value: datetime) -> str:
        # SQLite drops timezone information. Stored values are UTC.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str
    title: str
    snippet: str
    content: str
    search_query: str


class VerificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    explanation: str
    supporting_excerpt: str
    opposing_excerpt: str


class ClaimRead(BaseModel):
    id: uuid.UUID
    source_url: str
    text: str
    kind: str
    verification: VerificationRead | None = None


class ContradictionRead(BaseModel):
    explanation: str
    context: str
    claim_text: str
    other_claim_text: str
    source_url: str
    other_source_url: str


class FindingRead(BaseModel):
    text: str
    citation_urls: list[str]
    certainty: str


class ReportRead(BaseModel):
    summary: str
    findings: list[FindingRead]
    uncertainties: list[str]
    limitations: list[str]


class ResearchSessionRead(ResearchQuestionRead):
    sources: list[SourceRead]
    claims: list[ClaimRead]
    contradictions: list[ContradictionRead]
    report: ReportRead | None = None
