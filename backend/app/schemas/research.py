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
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float = 0
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_timestamp(self, value: datetime) -> str:
        # SQLite drops timezone information. Stored values are UTC.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class SourceQualityRead(BaseModel):
    role: str
    publisher: str
    author_known: bool
    date_known: bool
    specific: bool
    reports_original_data: bool
    reasons: list[str]


class SourceRead(BaseModel):
    id: uuid.UUID
    url: str
    title: str
    domain: str = ""
    snippet: str
    content: str
    search_query: str
    author: str = ""
    published_on: str = ""
    retrieved_at: datetime | None = None
    quality: SourceQualityRead

    @field_serializer("retrieved_at")
    def serialize_retrieved(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()


class VerificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    explanation: str
    supporting_excerpt: str
    opposing_excerpt: str


class EvidenceRead(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID | None = None
    source_url: str
    stance: str
    passage: str


class ClaimRead(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID | None = None
    source_url: str
    text: str
    kind: str
    review_status: str = "pending"
    verification: VerificationRead | None = None
    evidence: list[EvidenceRead] = Field(default_factory=list)


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


class GraphNodeRead(BaseModel):
    id: str
    kind: str
    label: str
    url: str = ""
    status: str = ""
    stance: str = ""
    passage: str = ""
    review_status: str = ""
    explanation: str = ""


class GraphEdgeRead(BaseModel):
    source: str
    target: str
    relation: str


class EvidenceGraphRead(BaseModel):
    nodes: list[GraphNodeRead]
    edges: list[GraphEdgeRead]


class ClaimDecision(BaseModel):
    claim_id: uuid.UUID
    decision: str

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        if value not in {"approved", "rejected"}:
            raise ValueError("Each claim must be approved or rejected.")
        return value


class ReviewRequest(BaseModel):
    action: str
    decisions: list[ClaimDecision] = Field(default_factory=list)
    note: str = Field(default="", max_length=500)

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        if value not in {"continue", "research_more"}:
            raise ValueError("Choose continue or research_more.")
        return value

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str) -> str:
        return " ".join(value.split())
