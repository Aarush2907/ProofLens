import inspect
import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.research.activity import emit
from app.research.checks import canonical_url
from app.research.contracts import SearchQueryPlan
from app.research.errors import ResearchError
from app.research.quality import domain_of


QUERY_SYSTEM = (
    "Turn the research question into one or two web search queries. "
    "Do not answer the question and do not invent sources."
)


def collect_sources(state: dict, model, search, fetch_page) -> dict:
    settings = get_settings()
    session_id = state.get("session_id") or ""
    emit("researcher_started", "Researcher agent started.", agent="researcher", session_id=session_id)
    queries = _search_queries(_question_for_search(state), model)
    hits = []
    for query in queries:
        emit(
            "searching",
            "Searching the web.",
            agent="researcher",
            detail={"query": query},
            session_id=session_id,
        )
        hits.extend(search(query, settings.max_search_results))

    sources = []
    seen = set()
    for hit in hits:
        url = canonical_url(hit.url)
        if not url or url in seen:
            continue
        seen.add(url)
        source_id = str(uuid.uuid4())
        fetched = _read_page(
            fetch_page,
            url,
            settings.source_content_chars,
            source_id=source_id,
            title=hit.title or url,
            session_id=session_id,
        )
        text, reused, outdated = _page_fields(fetched)
        content = text if len(text) >= 200 else (hit.content or hit.snippet)
        retrieved_at = datetime.now(timezone.utc).isoformat()
        if isinstance(fetched, dict) and fetched.get("retrieved_at"):
            retrieved_at = fetched["retrieved_at"]
        sources.append(
            {
                "id": source_id,
                "url": url,
                "title": hit.title or url,
                "snippet": hit.snippet,
                "content": (content or "")[: settings.source_content_chars],
                "search_query": hit.query,
                "domain": domain_of(url),
                "retrieved_at": retrieved_at,
                "published_on": hit.published_on or "",
                "author": hit.author or "",
            }
        )
        detail = {"url": url, "reused": reused, "possibly_outdated": outdated}
        if reused and outdated:
            message = f"Reused an older stored copy of {hit.title or url}. It may be outdated."
        elif reused:
            message = f"Reused a stored copy of {hit.title or url}."
        else:
            message = f"Source discovered: {hit.title or url}."
        emit("source_discovered", message, agent="researcher", detail=detail, session_id=session_id)
        if len(sources) >= settings.max_sources:
            break

    emit(
        "sources_collected",
        f"Collected {len(sources)} sources.",
        agent="researcher",
        detail={"count": len(sources)},
        session_id=session_id,
    )
    return {"sources": sources, "stage": "sources_collected", "research_more": False}


def _read_page(fetch_page, url: str, limit: int, **extra):
    accepted = inspect.signature(fetch_page).parameters
    kwargs = {key: value for key, value in extra.items() if key in accepted}
    if kwargs:
        return fetch_page(url, limit, **kwargs)
    return fetch_page(url, limit)


def _page_fields(fetched) -> tuple[str, bool, bool]:
    if isinstance(fetched, dict):
        return fetched.get("text") or "", bool(fetched.get("reused")), bool(fetched.get("possibly_outdated"))
    return fetched or "", False, False


def _question_for_search(state: dict) -> str:
    question = state["question"]
    note = (state.get("research_note") or "").strip()
    if not note:
        return question
    return f"{question}\nAdditional focus requested by the reviewer: {note}"


def _search_queries(question: str, model) -> list[str]:
    try:
        plan = model(SearchQueryPlan, QUERY_SYSTEM, question)
    except ResearchError:
        raise
    except Exception:
        # A planning failure should not hide sources the search API can return.
        return [question]

    queries = []
    for query in plan.queries:
        cleaned = " ".join(query.split())
        if cleaned and cleaned not in queries:
            queries.append(cleaned)
    return queries[:2] or [question]
