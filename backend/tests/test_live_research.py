import pytest

from app.core.config import get_settings
from app.research.graph import build_graph
from app.research.state import initial_state


@pytest.mark.e2e
def test_live_question_passes_through_the_agents():
    settings = get_settings()
    if not settings.openai_api_key or not settings.search_api_key:
        pytest.skip("Set OPENAI_API_KEY and SEARCH_API_KEY to run a live research question.")

    state = build_graph().invoke(
        initial_state("What evidence links consistent sleep to memory consolidation in adults?"),
        config={"recursion_limit": settings.graph_recursion_limit},
    )

    assert state["failed"] is False
    assert state["sources"]
    assert all(source["url"].startswith("http") for source in state["sources"])
    assert "writer" in state["trace"]
    assert state["report"]["summary"]
