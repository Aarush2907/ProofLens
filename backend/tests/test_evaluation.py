import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from app.evaluation.dataset import evaluation_cases
from app.evaluation.ragas_eval import ragas_report
from app.evaluation.runner import run_evaluation


def test_curated_evaluation_separates_a_quotation_from_a_true_claim():
    report = run_evaluation()
    by_id = {item["case_id"]: item["scores"] for item in report["cases"]}

    correct = by_id["correct-claim"]
    assert correct["citation_support"] == 1
    assert correct["claim_verification"] == 1
    assert correct["statistic_backing"] == 1
    assert correct["retrieval_quality"] == 1
    assert correct["context_relevance"] == 1
    assert correct["source_freshness"] == 1
    assert correct["answer_grounding"] > 0.5

    incorrect = by_id["incorrect-claim"]
    assert incorrect["citation_support"] == 1
    # The raw verdict was wrong. The product now refuses to call it Verified.
    assert incorrect["claim_verification"] == 1
    assert incorrect["statistic_backing"] == 0

    misleading = by_id["misleading-excerpt"]
    assert misleading["citation_support"] == 1
    assert misleading["claim_verification"] == 0
    # The denied figure is still inside the sentence, so number matching does not catch it.
    assert misleading["statistic_backing"] == 1

    assert by_id["unsupported-statistic"]["statistic_backing"] == 0
    assert by_id["unsupported-statistic"]["claim_verification"] == 1
    assert by_id["insufficient-evidence"]["claim_verification"] == 1
    assert by_id["contradictory-sources"]["claim_verification"] == 1
    assert by_id["contradictory-sources"]["citation_support"] == 1
    assert by_id["outdated-source"]["source_freshness"] == 1

    assert report["dataset_size"] == 7
    assert report["ragas"]["ran"] is False
    assert "does not guarantee" in report["limitation"]


def test_ragas_does_not_invent_a_score_without_a_key():
    report = ragas_report(evaluation_cases())

    assert report["ran"] is False
    assert "scores" not in report
    assert "OPENAI_API_KEY" in report["reason"]


@pytest.mark.skipif(importlib.util.find_spec("ragas") is None, reason="requirements-eval.txt is not installed")
def test_ragas_imports_in_a_separate_process():
    # Importing Ragas applies nest_asyncio, which breaks the API test client
    # in this process. The import is checked in a short-lived process instead.
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from app.evaluation.ragas_eval import load_ragas; "
                "evaluate, metrics = load_ragas(); "
                "assert [metric.name for metric in metrics] == "
                "['faithfulness', 'answer_relevancy', 'context_precision']; "
                "assert evaluate is not None"
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
