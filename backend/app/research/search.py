import logging

import httpx

from app.core.config import get_settings
from app.research.contracts import SearchHit
from app.research.errors import ResearchError

logger = logging.getLogger(__name__)


def hits_from_tavily(payload: dict, query: str) -> list[SearchHit]:
    hits = []
    for item in payload.get("results") or []:
        url = (item.get("url") or "").strip()
        if not url:
            continue
        snippet = (item.get("content") or "").strip()
        hits.append(
            SearchHit(
                title=((item.get("title") or url).strip())[:300],
                url=url,
                snippet=snippet[:1000],
                content=snippet,
                query=query,
            )
        )
    return hits


def search_web(query: str, limit: int) -> list[SearchHit]:
    settings = get_settings()
    if settings.search_provider != "tavily":
        raise ResearchError(
            f"Search provider '{settings.search_provider}' is not supported.",
            retryable=False,
        )
    if not settings.search_api_key:
        raise ResearchError("Search API key is not configured.", retryable=False)

    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.search_api_key,
                "query": query,
                "max_results": limit,
                "search_depth": "basic",
                "include_answer": False,
            },
            timeout=20,
        )
    except httpx.HTTPError as exc:
        logger.warning("Search request failed: %s", exc.__class__.__name__)
        raise ResearchError("The search request failed.", retryable=True) from exc

    if response.status_code in {401, 403}:
        raise ResearchError("The search API rejected the configured key.", retryable=False)
    if response.status_code >= 400:
        logger.warning("Search API returned status %s", response.status_code)
        raise ResearchError(
            "The search API request failed.",
            retryable=response.status_code >= 500 or response.status_code == 429,
        )
    return hits_from_tavily(response.json(), query)
