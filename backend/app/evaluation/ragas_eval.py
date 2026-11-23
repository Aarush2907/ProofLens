"""Optional Ragas scores. Missing credentials or a failed import produce no score.

Ragas 0.2.15 still imports a Vertex chat class that current LangChain no longer
ships. The shim below exists only so that import can succeed. It is not a
Vertex client, and this module never calls it.
"""

import sys
import types

from app.core.config import get_settings
from app.evaluation.dataset import EvalCase

_VERTEX = "langchain_community.chat_models.vertexai"
_NOTE = (
    "A Ragas score is a model judgment of these curated rows. "
    "It does not prove that a claim is factually correct."
)


def ragas_report(cases: list[EvalCase]) -> dict:
    if not get_settings().openai_api_key:
        return {
            "ran": False,
            "reason": (
                "OPENAI_API_KEY is not set, so Ragas faithfulness, answer relevancy, "
                "and context precision were not scored."
            ),
        }
    try:
        evaluate, metrics = load_ragas()
        from datasets import Dataset
    except Exception as exc:
        return _not_run(exc)

    rows = {
        "user_input": [case.question for case in cases],
        "response": [case.answer for case in cases],
        "retrieved_contexts": [[case.relevant_context] for case in cases],
        "reference": [case.relevant_context for case in cases],
    }
    try:
        result = evaluate(Dataset.from_dict(rows), metrics=metrics)
    except Exception as exc:
        return _not_run(exc)

    totals: dict[str, list[float]] = {}
    for row in getattr(result, "scores", []) or []:
        for name, value in row.items():
            if isinstance(value, (int, float)):
                totals.setdefault(name, []).append(float(value))
    scores = {name: round(sum(values) / len(values), 4) for name, values in totals.items() if values}
    return {"ran": True, "scores": scores, "note": _NOTE}


def load_ragas():
    _install_vertex_shim()
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, context_precision, faithfulness

    return evaluate, [faithfulness, answer_relevancy, context_precision]


def _install_vertex_shim() -> None:
    if _VERTEX in sys.modules:
        return
    try:
        __import__(_VERTEX)
    except ModuleNotFoundError:
        module = types.ModuleType(_VERTEX)

        class ChatVertexAI:
            """Placeholder. Ragas imports this name and does not construct it here."""

        module.ChatVertexAI = ChatVertexAI
        sys.modules[_VERTEX] = module


def _not_run(exc: Exception) -> dict:
    return {
        "ran": False,
        "reason": f"Ragas did not run ({exc.__class__.__name__}: {exc}). No score was invented.",
    }
