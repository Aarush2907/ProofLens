from app.research.checks import ground_verdict, statistic_is_backed

PASSAGE = "In the trial, 20 percent of 1,200 adults slept under six hours."


def _verdict(status: str, excerpt: str) -> dict:
    return {"status": status, "explanation": "Stated.", "supporting_excerpt": excerpt, "opposing_excerpt": ""}


def test_a_statistic_with_the_wrong_number_is_not_kept_as_verified():
    raw = _verdict("Verified", "20 percent of 1,200 adults slept under six hours")

    result = ground_verdict(raw, PASSAGE, "80 percent of adults slept under six hours.", "statistic")

    assert result["status"] == "Insufficient evidence"
    assert "figure" in result["explanation"]


def test_a_statistic_whose_number_is_quoted_stays_verified():
    raw = _verdict("Verified", "20 percent of 1,200 adults slept under six hours")

    result = ground_verdict(raw, PASSAGE, "20 percent of adults slept under six hours.", "statistic")

    assert result["status"] == "Verified"


def test_numbers_match_when_the_claim_and_quote_format_thousands_differently():
    assert statistic_is_backed("About 1200 adults took part.", "1,200 adults took part") is True
    assert statistic_is_backed("About 1,500 adults took part.", "1,200 adults took part") is False


def test_a_claim_that_is_not_a_statistic_is_not_checked_for_numbers():
    raw = _verdict("Verified", "20 percent of 1,200 adults slept under six hours")

    result = ground_verdict(raw, PASSAGE, "Short sleep is common.", "fact")

    assert result["status"] == "Verified"
