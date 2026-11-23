"""Deterministic checks used when a model judge is unavailable.

A score of 1 means the row agreed with the rule or the label. It does not mean
the claim is true in the world. Citation support only asks whether the quoted
words occur in the passage.
"""

import re

from app.evaluation.dataset import EvalCase
from app.research.checks import (
    GROUNDED_STATUSES,
    ground_verdict,
    normalise_status,
    passage_contains,
    statistic_is_backed,
)
from app.research.embeddings import HashingEmbedder
from app.research.index import is_outdated

_TOKEN = re.compile(r"[a-z0-9]+")


def score_case(case: EvalCase) -> dict[str, float]:
    scores = {
        "citation_support": citation_support(case),
        "claim_verification": claim_verification(case),
        "retrieval_quality": retrieval_quality(case),
        "context_relevance": context_relevance(case),
        "answer_grounding": answer_grounding(case),
        "source_freshness": source_freshness(case),
    }
    statistic = statistic_backing(case)
    if statistic is not None:
        scores["statistic_backing"] = statistic
    return scores


def citation_support(case: EvalCase) -> float:
    status = normalise_status(case.verdict.get("status", ""))
    if status in GROUNDED_STATUSES:
        return _contained(case.verdict.get("supporting_excerpt") or "", case.passage)
    if status == "Contradicted":
        return _contained(case.verdict.get("opposing_excerpt") or "", case.passage)
    return 1.0


def claim_verification(case: EvalCase) -> float:
    grounded = ground_verdict(case.verdict, case.passage, case.claim, case.claim_kind)
    return 1.0 if grounded["status"] == case.expected_status else 0.0


def retrieval_quality(case: EvalCase) -> float:
    embedder = HashingEmbedder()
    query, relevant, distractor = embedder.embed(
        [case.retrieval_query, case.relevant_context, case.distractor]
    )
    relevant_score = _dot(query, relevant)
    distractor_score = _dot(query, distractor)
    if relevant_score >= 0.2 and relevant_score > distractor_score:
        return 1.0
    return 0.0


def context_relevance(case: EvalCase) -> float:
    question = _tokens(case.question)
    if not question:
        return 0.0
    relevant = len(question & _tokens(case.relevant_context)) / len(question)
    distractor = len(question & _tokens(case.distractor)) / len(question)
    if relevant > distractor and relevant > 0:
        return 1.0
    return 0.0


def answer_grounding(case: EvalCase) -> float:
    words = _tokens(case.answer)
    if not words:
        return 0.0
    context = _tokens(case.passage) | _tokens(case.relevant_context)
    return round(len(words & context) / len(words), 4)


def source_freshness(case: EvalCase) -> float:
    return 1.0 if is_outdated(case.retrieved_at) == case.expects_outdated else 0.0


def statistic_backing(case: EvalCase) -> float | None:
    """Score the checker's raw verdict, before grounding.

    Every number in a supported statistic should appear in its excerpt. A 0
    means the raw verdict needed the product's guard to be downgraded. This
    does not catch a sentence that names the figure in order to deny it.
    """

    if case.claim_kind != "statistic":
        return None
    status = normalise_status(case.verdict.get("status", ""))
    if status not in GROUNDED_STATUSES:
        return 1.0
    excerpt = case.verdict.get("supporting_excerpt") or ""
    return 1.0 if statistic_is_backed(case.claim, excerpt) else 0.0


def _contained(excerpt: str, passage: str) -> float:
    return 1.0 if passage_contains(excerpt, passage) else 0.0


def _tokens(text: str) -> set[str]:
    return {token for token in _TOKEN.findall(text.lower()) if len(token) > 3}


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))
