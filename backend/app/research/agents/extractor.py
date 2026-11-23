import uuid

from app.core.config import get_settings
from app.research.activity import emit
from app.research.checks import filter_claims
from app.research.contracts import ClaimBatch
from app.research.safety import DATA_RULE, untrusted


SYSTEM = (
    "Extract checkable statements from the supplied sources. "
    "Copy source_url from the sources. "
    "Use kind opinion for judgments and predictions. "
    "Use fact, statistic, or date for statements a passage can support or contradict. "
    "Do not add a statement that is not in the supplied text. "
    + DATA_RULE
)


def extract_claims(state: dict, model, drafts: list[dict] | None = None) -> dict:
    session_id = state.get("session_id") or ""
    emit("extractor_started", "Extractor started.", agent="extractor", session_id=session_id)
    if not state.get("sources"):
        emit(
            "claims_extracted",
            "No claims were extracted.",
            agent="extractor",
            detail={"count": 0},
            session_id=session_id,
        )
        return {"claims": [], "stage": "claims_extracted"}

    if drafts is None:
        user = _source_packet(state["sources"])
        batch = model(ClaimBatch, SYSTEM, user)
        drafts = [claim.model_dump() for claim in batch.claims]
    claims = filter_claims(drafts, state["sources"], get_settings().max_claims)
    sources_by_url = {source["url"]: source for source in state["sources"]}
    for claim in claims:
        claim["id"] = str(uuid.uuid4())
        source = sources_by_url.get(claim["source_url"]) or {}
        claim["source_id"] = source.get("id") or ""
        claim["review_status"] = "pending"
    emit(
        "claims_extracted",
        f"Extracted {len(claims)} claims.",
        agent="extractor",
        detail={"count": len(claims)},
        session_id=session_id,
    )
    return {"claims": claims, "stage": "claims_extracted"}


def _source_packet(sources: list[dict]) -> str:
    blocks = []
    for source in sources:
        passage = source.get("content") or source.get("snippet") or ""
        blocks.append(
            f"URL: {source['url']}\nTitle: {untrusted(source.get('title', ''))}\n"
            f"Passage:\n{untrusted(passage[:2500])}"
        )
    return "\n\n".join(blocks)
