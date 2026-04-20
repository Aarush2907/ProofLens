"""Run one live question and print the structured report.

From the backend directory:

    python -m app.research.live "Your research question"

This calls the configured OpenAI model and search API. It does not invent a
report when those services are not configured.
"""

import json
import sys

from app.research.errors import ResearchError
from app.research.graph import build_graph
from app.research.state import initial_state


def main() -> int:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Usage: python -m app.research.live \"research question\"", file=sys.stderr)
        return 2
    question = sys.argv[1].strip()
    try:
        state = build_graph().invoke(initial_state(question))
    except ResearchError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if state.get("failed"):
        print(state.get("last_error") or "Research failed.", file=sys.stderr)
        return 1
    print(json.dumps(_public_result(state), indent=2))
    return 0


def _public_result(state: dict) -> dict:
    return {
        "question": state["question"],
        "sources": [
            {"title": source["title"], "url": source["url"], "search_query": source["search_query"]}
            for source in state.get("sources") or []
        ],
        "claims": state.get("claims") or [],
        "verifications": state.get("verifications") or [],
        "contradictions": state.get("contradictions") or [],
        "report": state.get("report"),
        "trace": state.get("trace") or [],
    }


if __name__ == "__main__":
    raise SystemExit(main())
