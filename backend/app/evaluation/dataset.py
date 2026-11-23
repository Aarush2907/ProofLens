"""Curated rows for the evaluation that always runs without an API key.

Each row is a labelled situation: a correct claim, a wrong claim, sources that
disagree, a passage that is too thin, an old retrieval time, a quotation that
is real but about a different fact, and a statistic the excerpt does not contain.
The labels are the expected judgment. They are not a proof that the passage is
true outside this dataset.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


SLEEP = (
    "A randomised trial of 120 adults reported that 20 percent slept under six hours on weeknights."
)
SLEEP_OTHER = (
    "A clinic audit of night shifts reported that 5 percent of adults slept under six hours on weeknights."
)
STEEL = "Steel production at the coastal mills rose after the tariff."


def _days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    category: str
    question: str
    claim: str
    claim_kind: str
    passage: str
    retrieval_query: str
    relevant_context: str
    distractor: str
    verdict: dict
    expected_status: str
    answer: str
    retrieved_at: str
    expects_outdated: bool


def evaluation_cases() -> list[EvalCase]:
    fresh = _days_ago(2)
    stale = _days_ago(40)
    return [
        EvalCase(
            case_id="correct-claim",
            category="correct",
            question="What share of adults in the trial slept under six hours?",
            claim="In the trial, 20 percent of adults slept under six hours.",
            claim_kind="statistic",
            passage=SLEEP,
            retrieval_query="What share of adults in the trial slept under six hours?",
            relevant_context=SLEEP,
            distractor=STEEL,
            verdict={
                "status": "Verified",
                "supporting_excerpt": "20 percent slept under six hours on weeknights",
                "opposing_excerpt": "",
                "explanation": "The trial passage states this figure.",
            },
            expected_status="Verified",
            answer="The trial reported that 20 percent of adults slept under six hours on weeknights.",
            retrieved_at=fresh,
            expects_outdated=False,
        ),
        EvalCase(
            case_id="incorrect-claim",
            category="incorrect",
            question="Did the trial find that most adults slept under six hours?",
            claim="In the trial, 80 percent of adults slept under six hours.",
            claim_kind="statistic",
            passage=SLEEP,
            retrieval_query="Did the trial find that most adults slept under six hours?",
            relevant_context=SLEEP,
            distractor=STEEL,
            verdict={
                "status": "Verified",
                "supporting_excerpt": "20 percent slept under six hours on weeknights",
                "opposing_excerpt": "",
                "explanation": "A quotation was copied, but it does not state 80 percent.",
            },
            # The raw verdict is wrong. The safe outcome is that the product refuses to call it Verified.
            expected_status="Insufficient evidence",
            answer="The trial found that 80 percent of adults slept under six hours.",
            retrieved_at=fresh,
            expects_outdated=False,
        ),
        EvalCase(
            case_id="contradictory-sources",
            category="contradictory",
            question="What share of adults slept under six hours?",
            claim="Five percent of adults slept under six hours on weeknights.",
            claim_kind="statistic",
            passage=SLEEP + " " + SLEEP_OTHER,
            retrieval_query="What share of adults slept under six hours on weeknights?",
            relevant_context=SLEEP_OTHER,
            distractor=STEEL,
            verdict={
                "status": "Contradicted",
                "supporting_excerpt": "",
                "opposing_excerpt": "20 percent slept under six hours on weeknights",
                "explanation": "The trial reports 20 percent, which conflicts with 5 percent.",
            },
            expected_status="Contradicted",
            answer="The collected sources disagree on the share of adults who slept under six hours.",
            retrieved_at=fresh,
            expects_outdated=False,
        ),
        EvalCase(
            case_id="insufficient-evidence",
            category="insufficient",
            question="What share of adults in the trial slept under six hours?",
            claim="In the trial, 20 percent of adults slept under six hours.",
            claim_kind="statistic",
            passage="Chart.",
            retrieval_query="What share of adults in the trial slept under six hours?",
            relevant_context=SLEEP,
            distractor=STEEL,
            verdict={
                "status": "Insufficient evidence",
                "supporting_excerpt": "",
                "opposing_excerpt": "",
                "explanation": "The source did not include a passage long enough to check this claim.",
            },
            expected_status="Insufficient evidence",
            answer="The collected page does not contain a passage that can support a figure.",
            retrieved_at=fresh,
            expects_outdated=False,
        ),
        EvalCase(
            case_id="outdated-source",
            category="outdated",
            question="What share of adults in the trial slept under six hours?",
            claim="In the trial, 20 percent of adults slept under six hours.",
            claim_kind="statistic",
            passage=SLEEP,
            retrieval_query="What share of adults in the trial slept under six hours?",
            relevant_context=SLEEP,
            distractor=STEEL,
            verdict={
                "status": "Verified",
                "supporting_excerpt": "20 percent slept under six hours on weeknights",
                "opposing_excerpt": "",
                "explanation": "The quotation matches, and the copy is older than the freshness window.",
            },
            expected_status="Verified",
            answer="An older copy of the trial report says 20 percent of adults slept under six hours.",
            retrieved_at=stale,
            expects_outdated=True,
        ),
        EvalCase(
            case_id="misleading-excerpt",
            category="misleading",
            question="Did the paper find that 80 percent slept under six hours?",
            claim="The paper found that 80 percent of adults slept under six hours.",
            claim_kind="statistic",
            passage=(
                "The paper did not find that 80 percent of adults slept under six hours. "
                "A randomised trial of 120 adults reported that 20 percent slept under six hours on weeknights."
            ),
            retrieval_query="Did the paper find that 80 percent of adults slept under six hours?",
            relevant_context=SLEEP,
            distractor=STEEL,
            verdict={
                "status": "Verified",
                "supporting_excerpt": "80 percent of adults slept under six hours",
                "opposing_excerpt": "",
                "explanation": "The words appear in the page, inside a sentence that denies them.",
            },
            expected_status="Insufficient evidence",
            answer="The paper found that 80 percent of adults slept under six hours.",
            retrieved_at=fresh,
            expects_outdated=False,
        ),
        EvalCase(
            case_id="unsupported-statistic",
            category="unsupported_statistic",
            question="What share of adults in the trial slept under six hours?",
            claim="In the trial, 47 percent of adults slept under six hours.",
            claim_kind="statistic",
            passage="Adults in the trial were asked about their weeknight sleep habits.",
            retrieval_query="What share of adults in the trial slept under six hours?",
            relevant_context="Adults in the trial were asked about their weeknight sleep habits.",
            distractor=STEEL,
            verdict={
                "status": "Verified",
                "supporting_excerpt": "Adults in the trial were asked about their weeknight sleep habits",
                "opposing_excerpt": "",
                "explanation": "The excerpt is from the page and does not contain 47 percent.",
            },
            expected_status="Insufficient evidence",
            answer="The trial page says adults were asked about sleep, and it does not state 47 percent.",
            retrieved_at=fresh,
            expects_outdated=False,
        ),
    ]
