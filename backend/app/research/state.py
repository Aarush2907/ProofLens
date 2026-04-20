import operator
from typing import Annotated, Literal, TypedDict

ClaimKind = Literal["fact", "statistic", "date", "opinion"]
VerificationStatus = Literal[
    "Verified",
    "Partially supported",
    "Contradicted",
    "Insufficient evidence",
]
FindingCertainty = Literal["supported", "partial", "uncertain"]


class ResearchState(TypedDict):
    question: str
    sources: list[dict]
    claims: list[dict]
    verifications: list[dict]
    contradictions: list[dict]
    report: dict | None
    retries: dict[str, int]
    last_error: str
    error_retryable: bool
    failed: bool
    stage: str
    trace: Annotated[list[str], operator.add]


def initial_state(question: str) -> ResearchState:
    return {
        "question": question,
        "sources": [],
        "claims": [],
        "verifications": [],
        "contradictions": [],
        "report": None,
        "retries": {},
        "last_error": "",
        "error_retryable": True,
        "failed": False,
        "stage": "researching",
        "trace": [],
    }
