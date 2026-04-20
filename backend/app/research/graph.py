import logging

from langgraph.graph import END, START, StateGraph

from app.core.config import get_settings
from app.research.agents.contradiction_detector import find_contradictions
from app.research.agents.extractor import extract_claims
from app.research.agents.fact_checker import check_claims
from app.research.agents.researcher import collect_sources
from app.research.agents.writer import write_report
from app.research.errors import ResearchError
from app.research.model import parse_model
from app.research.pages import fetch_page_text
from app.research.search import search_web
from app.research.state import ResearchState

logger = logging.getLogger(__name__)


def build_graph(model=None, search=None, fetch_page=None):
    """Compile the five-agent graph.

    model, search, and fetch_page can be replaced in tests. The defaults call
    the configured OpenAI and search APIs and retrieve source pages.
    """

    model = model or parse_model
    search = search or search_web
    fetch_page = fetch_page or fetch_page_text

    def researcher(state: ResearchState) -> dict:
        return collect_sources(state, model, search, fetch_page)

    def extractor(state: ResearchState) -> dict:
        return extract_claims(state, model)

    def fact_checker(state: ResearchState) -> dict:
        return check_claims(state, model)

    def contradiction_detector(state: ResearchState) -> dict:
        return find_contradictions(state, model)

    def writer(state: ResearchState) -> dict:
        return write_report(state, model)

    graph = StateGraph(ResearchState)
    graph.add_node("researcher", _guard("researcher", researcher))
    graph.add_node("extractor", _guard("extractor", extractor))
    graph.add_node("fact_checker", _guard("fact_checker", fact_checker))
    graph.add_node("contradiction_detector", _guard("contradiction_detector", contradiction_detector))
    graph.add_node("writer", _guard("writer", writer))
    graph.add_node("fail", _fail)

    graph.add_edge(START, "researcher")
    graph.add_conditional_edges(
        "researcher",
        _route("researcher", _after_researcher),
        {
            "researcher": "researcher",
            "extractor": "extractor",
            "writer": "writer",
            "fail": "fail",
        },
    )
    graph.add_conditional_edges(
        "extractor",
        _route("extractor", _after_extractor),
        {
            "extractor": "extractor",
            "fact_checker": "fact_checker",
            "writer": "writer",
            "fail": "fail",
        },
    )
    graph.add_conditional_edges(
        "fact_checker",
        _route("fact_checker", lambda _state: "contradiction_detector"),
        {
            "fact_checker": "fact_checker",
            "contradiction_detector": "contradiction_detector",
            "fail": "fail",
        },
    )
    graph.add_conditional_edges(
        "contradiction_detector",
        _route("contradiction_detector", lambda _state: "writer"),
        {
            "contradiction_detector": "contradiction_detector",
            "writer": "writer",
            "fail": "fail",
        },
    )
    graph.add_conditional_edges(
        "writer",
        _route("writer", lambda _state: "end"),
        {"writer": "writer", "end": END, "fail": "fail"},
    )
    graph.add_edge("fail", END)
    return graph.compile()


def _guard(name: str, agent):
    def node(state: ResearchState) -> dict:
        try:
            update = agent(state)
        except ResearchError as exc:
            logger.warning("Agent %s stopped: %s", name, exc)
            return _failure(state, name, str(exc), exc.retryable)
        except Exception:
            logger.exception("Agent %s failed", name)
            return _failure(state, name, f"The {name.replace('_', ' ')} could not finish.", True)
        update = dict(update)
        update["last_error"] = ""
        update["error_retryable"] = True
        update["trace"] = [name]
        return update

    return node


def _failure(state: ResearchState, name: str, message: str, retryable: bool) -> dict:
    retries = dict(state.get("retries") or {})
    retries[name] = retries.get(name, 0) + 1
    return {
        "retries": retries,
        "last_error": message,
        "error_retryable": retryable,
        "trace": [f"{name}:error"],
    }


def _fail(state: ResearchState) -> dict:
    return {"failed": True, "stage": "failed", "trace": ["fail"]}


def _route(name: str, on_success):
    def route(state: ResearchState) -> str:
        if state.get("last_error"):
            attempts = (state.get("retries") or {}).get(name, 0)
            if state.get("error_retryable", True) and attempts < get_settings().agent_max_attempts:
                return name
            return "fail"
        return on_success(state)

    return route


def _after_researcher(state: ResearchState) -> str:
    if state.get("sources"):
        return "extractor"
    return "writer"


def _after_extractor(state: ResearchState) -> str:
    if state.get("claims"):
        return "fact_checker"
    return "writer"
