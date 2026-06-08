"""Tool bodies used by the MCP server.

The agents decide what to ask. These functions do the work and return data.
They do not choose the next research step.
"""

import uuid
from datetime import datetime, timezone

from app.research.checks import canonical_url
from app.research.contracts import ClaimBatch, Verdict
from app.research.errors import ResearchError
from app.research.index import get_index
from app.research.model import parse_model
from app.research.pages import fetch_page_text
from app.research.search import search_web as search_provider

EXTRACT_SYSTEM = (
    "Extract checkable statements from the supplied sources. "
    "Copy source_url from the sources. "
    "Use kind opinion for judgments and predictions. "
    "Use fact, statistic, or date for statements a passage can support or contradict. "
    "Do not add a statement that is not in the supplied text."
)

VERIFY_SYSTEM = (
    "Check one claim against one source passage. "
    "Use Verified only when the passage directly states the claim. "
    "Use Partially supported when the passage supports only part of the claim. "
    "Use Contradicted when the passage conflicts with the claim. "
    "Otherwise use Insufficient evidence. "
    "supporting_excerpt and opposing_excerpt must be copied from the passage."
)


class ToolInputError(ValueError):
    """The tool was called with arguments that cannot be executed."""


def search_web(query: str, limit: int = 5) -> dict:
    query = _query(query)
    limit = _limit(limit)
    hits = search_provider(query, limit)
    return {
        "results": [
            {
                "title": hit.title,
                "url": hit.url,
                "snippet": hit.snippet,
                "published_on": hit.published_on,
                "author": hit.author,
                "query": hit.query,
            }
            for hit in hits
        ]
    }


def retrieve_source(
    url: str,
    limit: int = 4000,
    session_id: str = "",
    source_id: str = "",
    title: str = "",
) -> dict:
    canonical = canonical_url(url)
    if not canonical:
        raise ToolInputError("url must be an http or https address.")
    limit = _limit(limit, upper=20000)
    session = _optional_uuid(session_id, "session_id")
    source = _optional_uuid(source_id, "source_id") or str(uuid.uuid4())
    stored = get_index().lookup_url(canonical)
    reused = False
    outdated = False
    retrieved_at = datetime.now(timezone.utc).isoformat()
    if stored and stored.get("text") and not stored.get("possibly_outdated"):
        text = stored["text"]
        reused = True
        retrieved_at = stored.get("retrieved_at") or retrieved_at
    else:
        text = fetch_page_text(canonical, limit)
        if not text and stored and stored.get("text"):
            text = stored["text"]
            reused = True
            outdated = True
            retrieved_at = stored.get("retrieved_at") or retrieved_at
    text = (text or "")[:limit]
    if session and text:
        get_index().upsert_source(
            session,
            {
                "id": source,
                "url": canonical,
                "title": title or (stored or {}).get("title") or canonical,
                "content": text,
                "retrieved_at": retrieved_at,
            },
        )
    return {
        "url": canonical,
        "title": title or (stored or {}).get("title") or canonical,
        "text": text,
        "source_id": source,
        "reused": reused,
        "possibly_outdated": outdated,
        "retrieved_at": retrieved_at,
    }


def extract_claims(sources: list[dict]) -> dict:
    if not isinstance(sources, list) or not sources:
        raise ToolInputError("sources must be a non-empty list.")
    blocks = []
    for source in sources:
        if not isinstance(source, dict):
            raise ToolInputError("Each source must be an object.")
        url = canonical_url(source.get("url") or "")
        text = " ".join(str(source.get("text") or source.get("content") or "").split())
        if not url or len(text) < 24:
            continue
        blocks.append(f"URL: {url}\nTitle: {source.get('title') or ''}\nPassage:\n{text[:2500]}")
    if not blocks:
        return {"claims": []}
    batch = parse_model(ClaimBatch, EXTRACT_SYSTEM, "\n\n".join(blocks))
    return {
        "claims": [
            {"source_url": claim.source_url, "text": claim.text, "kind": claim.kind}
            for claim in batch.claims
        ]
    }


def verify_claim(claim: str, passage: str) -> dict:
    claim_text = " ".join((claim or "").split())
    passage_text = passage or ""
    if len(claim_text) < 12:
        raise ToolInputError("claim must be at least 12 characters.")
    if len(" ".join(passage_text.split())) < 24:
        return {
            "status": "Insufficient evidence",
            "explanation": "The source did not include a passage long enough to check this claim.",
            "supporting_excerpt": "",
            "opposing_excerpt": "",
        }
    verdict = parse_model(
        Verdict,
        VERIFY_SYSTEM,
        f"Claim: {claim_text}\n\nPassage:\n{passage_text[:5000]}",
    )
    return verdict.model_dump()


def search_evidence(query: str, session_id: str, limit: int = 4) -> dict:
    query_text = _query(query)
    session = _optional_uuid(session_id, "session_id")
    if not session:
        raise ToolInputError("session_id must be a UUID.")
    limit = _limit(limit, upper=8)
    try:
        passages = get_index().search(query_text, session, limit)
    except ResearchError:
        raise
    except Exception as exc:
        raise ResearchError("Evidence search failed.", retryable=True) from exc
    return {"passages": passages}


def _query(query: str) -> str:
    cleaned = " ".join((query or "").split())
    if not cleaned:
        raise ToolInputError("query is required.")
    if len(cleaned) > 400:
        raise ToolInputError("query is too long.")
    return cleaned


def _limit(limit: int, upper: int = 10) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError) as exc:
        raise ToolInputError("limit must be an integer.") from exc
    if value < 1 or value > upper:
        raise ToolInputError(f"limit must be between 1 and {upper}.")
    return value


def _optional_uuid(value: str, name: str) -> str:
    if value is None or str(value).strip() == "":
        return ""
    try:
        return str(uuid.UUID(str(value)))
    except ValueError as exc:
        raise ToolInputError(f"{name} must be a UUID.") from exc
