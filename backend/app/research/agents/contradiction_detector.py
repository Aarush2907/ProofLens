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
    return {
        "contradictions": filter_contradictions(disagreements, state["claims"]),
        "stage": "contradictions_checked",
    }
