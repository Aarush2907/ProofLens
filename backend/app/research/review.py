from langgraph.types import interrupt

from app.research.activity import emit

# A reviewer can send the researcher back twice. After that the run stops
# instead of looping on the same question.
MAX_EXTRA_ROUNDS = 2


def review_claims(state: dict) -> dict:
    emit(
        "approval_required",
        "Approval required before the report is written.",
        agent="review",
        detail={"claim_count": len(state.get("claims") or [])},
        session_id=state.get("session_id") or "",
    )
    decision = interrupt(
        {
            "question": state.get("question") or "",
            "claim_ids": [claim["id"] for claim in state.get("claims") or []],
        }
    )
    if not isinstance(decision, dict):
        decision = {}
    return apply_review(state, decision)


def apply_review(state: dict, decision: dict) -> dict:
    action = decision.get("action")
    if action == "research_more":
        rounds = int(state.get("review_rounds") or 0) + 1
        if rounds > MAX_EXTRA_ROUNDS:
            return {
                "last_error": "Additional research was already requested twice for this question.",
                "error_retryable": False,
                "research_more": False,
            }
        return {
            "review_rounds": rounds,
            "research_note": (decision.get("note") or "").strip(),
            "research_more": True,
            "sources": [],
            "claims": [],
            "verifications": [],
            "contradictions": [],
            "report": None,
            "stage": "researching",
            "last_error": "",
            "error_retryable": True,
        }

    choices = {
        str(item.get("claim_id")): item.get("decision")
        for item in decision.get("decisions") or []
    }
    claims = []
    for claim in state.get("claims") or []:
        updated = dict(claim)
        choice = choices.get(claim["id"])
        updated["review_status"] = choice if choice in {"approved", "rejected"} else "rejected"
        claims.append(updated)
    return {
        "claims": claims,
        "research_more": False,
        "stage": "claims_reviewed",
        "last_error": "",
        "error_retryable": True,
    }
