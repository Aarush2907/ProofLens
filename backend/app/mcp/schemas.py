from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    published_on: str = ""
    author: str = ""
    query: str = ""


class SearchWebOutput(BaseModel):
    results: list[SearchResult]


class RetrieveSourceOutput(BaseModel):
    url: str
    title: str = ""
    text: str = ""
    source_id: str = ""
    reused: bool = False
    possibly_outdated: bool = False
    retrieved_at: str = ""


class ExtractedClaimOutput(BaseModel):
    source_url: str
    text: str
    kind: str


class ExtractClaimsOutput(BaseModel):
    claims: list[ExtractedClaimOutput]


class VerifyClaimOutput(BaseModel):
    status: str
    explanation: str
    supporting_excerpt: str = ""
    opposing_excerpt: str = ""


class EvidencePassageOutput(BaseModel):
    text: str
    url: str
    title: str = ""
    source_id: str = ""
    session_id: str = ""
    score: float = 0
    retrieved_at: str = ""
    possibly_outdated: bool = False
    from_memory: bool = False


class SearchEvidenceOutput(BaseModel):
    passages: list[EvidencePassageOutput] = Field(default_factory=list)
