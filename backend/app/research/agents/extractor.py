import uuid

from app.core.config import get_settings
from app.research.checks import filter_claims
from app.research.contracts import ClaimBatch


SYSTEM = (
    "Extract checkable statements from the supplied sources. "
    "Copy source_url from the sources. "
    "Use kind opinion for judgments and predictions. "
    "Use fact, statistic, or date for statements a passage can support or contradict. "
    "Do not add a statement that is not in the supplied text."
)


def extract_claims(state: dict, model) -> dict:
    if not state.get("sources"):
        return {"claims": [], "stage": "claims_extracted"}

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
    return {"claims": claims, "stage": "claims_extracted"}


def _source_packet(sources: list[dict]) -> str:
    blocks = []
    for source in sources:
        passage = source.get("content") or source.get("snippet") or ""
        blocks.append(
            f"URL: {source['url']}\nTitle: {source.get('title', '')}\nPassage:\n{passage[:2500]}"
        )
    return "\n\n".join(blocks)
