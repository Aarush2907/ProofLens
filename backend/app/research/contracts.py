from typing import Literal

from pydantic import BaseModel, Field

from app.research.state import ClaimKind, FindingCertainty, VerificationStatus


class SearchQueryPlan(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=2)


class SearchHit(BaseModel):
    title: str
    url: str
    snippet: str = ""
    content: str = ""
    query: str
    published_on: str = ""
    author: str = ""


class ExtractedClaim(BaseModel):
    source_url: str
    text: str
    kind: ClaimKind


class ClaimBatch(BaseModel):
    claims: list[ExtractedClaim]


class Verdict(BaseModel):
    status: VerificationStatus
    explanation: str
    supporting_excerpt: str = ""
    opposing_excerpt: str = ""


class Disagreement(BaseModel):
    claim_id_a: str
    claim_id_b: str
    kind: Literal[
        "factual_disagreement",
        "conflicting_number_or_date",
        "different_definition",
        "different_publication_date",
        "not_a_contradiction",
    ]
    explanation: str
    context: str = ""


class DisagreementBatch(BaseModel):
    disagreements: list[Disagreement]


class FindingDraft(BaseModel):
    text: str
    citation_urls: list[str]
    certainty: FindingCertainty


class ReportDraft(BaseModel):
    summary: str
    findings: list[FindingDraft]
    uncertainties: list[str]
    limitations: list[str]
