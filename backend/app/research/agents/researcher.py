import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
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
    queries = _search_queries(_question_for_search(state), model)
    hits = []
    for query in queries:
        hits.extend(search(query, settings.max_search_results))

    sources = []
    seen = set()
    for hit in hits:
        url = canonical_url(hit.url)
        if not url or url in seen:
            continue
        seen.add(url)
        fetched = fetch_page(url, settings.source_content_chars)
        content = fetched if len(fetched) >= 200 else (hit.content or hit.snippet)
        sources.append(
            {
                "id": str(uuid.uuid4()),
                "url": url,
                "title": hit.title or url,
                "snippet": hit.snippet,
                "content": (content or "")[: settings.source_content_chars],
                "search_query": hit.query,
                "domain": domain_of(url),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "published_on": hit.published_on or "",
                "author": hit.author or "",
            }
        )
        if len(sources) >= settings.max_sources:
            break

    return {"sources": sources, "stage": "sources_collected", "research_more": False}


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
