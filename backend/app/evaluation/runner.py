"""Run the curated evaluation and, when a key is configured, Ragas.

The means below are agreement with this dataset and with the quotation rules.
A high mean does not guarantee that a research report is factually correct.
"""

from app.evaluation.dataset import evaluation_cases
from app.evaluation.metrics import score_case
from app.evaluation.ragas_eval import ragas_report

LIMITATION = (
    "These scores measure the curated rows: whether a quotation appears in the supplied passage, "
    "whether the grounded verdict matches the label, and whether retrieval prefers the labelled passage. "
    "A high score does not guarantee that a claim is factually correct, current, or complete."
)


def run_evaluation() -> dict:
    cases = evaluation_cases()
    scored = []
    totals: dict[str, list[float]] = {}
    for case in cases:
        scores = score_case(case)
        for name, value in scores.items():
            totals.setdefault(name, []).append(value)
        scored.append(
            {
                "case_id": case.case_id,
                "category": case.category,
                "scores": scores,
            }
        )
    means = {name: round(sum(values) / len(values), 4) for name, values in totals.items()}
    return {
        "dataset_size": len(cases),
        "metrics": means,
        "cases": scored,
        "ragas": ragas_report(cases),
        "limitation": LIMITATION,
    }
