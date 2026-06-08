from app.research.activity import emit
from app.research.checks import filter_contradictions
from app.research.contracts import DisagreementBatch


SYSTEM = (
    "Compare claims that come from different sources. "
    "Report a disagreement only when two claims cannot both be true. "
    "Do not treat a different publication date, a different definition, or a different population "
    "as a contradiction. "
    "Use kind different_definition or different_publication_date when that is the only difference, "
    "and those will be discarded."
)


def find_contradictions(state: dict, model) -> dict:
    session_id = state.get("session_id") or ""
    emit(
        "contradiction_detector_started",
        "Contradiction detector started.",
        agent="contradiction_detector",
        session_id=session_id,
    )
    comparable = [
        claim
        for claim in state.get("claims") or []
        if claim.get("kind") != "opinion"
    ]
    urls = {claim["source_url"] for claim in comparable}
    if len(comparable) < 2 or len(urls) < 2:
        return {"contradictions": [], "stage": "contradictions_checked"}

    lines = []
    for claim in comparable:
        lines.append(f"{claim['id']} | {claim['source_url']} | {claim['text']}")
    batch = model(DisagreementBatch, SYSTEM, "\n".join(lines))
    disagreements = [item.model_dump() for item in batch.disagreements]
    contradictions = filter_contradictions(disagreements, state["claims"])
    for item in contradictions:
        emit(
            "contradiction_detected",
            item["explanation"],
            agent="contradiction_detector",
            detail={"claim_id": item["claim_id"], "other_claim_id": item["other_claim_id"]},
            session_id=session_id,
        )
    return {"contradictions": contradictions, "stage": "contradictions_checked"}
