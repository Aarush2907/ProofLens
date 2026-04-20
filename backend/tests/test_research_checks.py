from app.research.checks import (
    canonical_url,
    filter_claims,
    filter_contradictions,
    filter_report,
    ground_verdict,
)
from app.research.pages import text_from_html
from app.research.search import hits_from_tavily


PASSAGE = "Adults who slept seven hours recalled 20 percent more word pairs than adults who slept four hours."


def test_canonical_url_ignores_www_and_trailing_slash():
    assert canonical_url("HTTPS://WWW.Example.edu/sleep/") == "https://example.edu/sleep"


def test_grounded_verdict_must_quote_the_passage():
    invented = ground_verdict(
        {
            "status": "Verified",
            "explanation": "Looks true.",
            "supporting_excerpt": "This sentence was not in the source.",
            "opposing_excerpt": "",
        },
        PASSAGE,
    )
    assert invented["status"] == "Insufficient evidence"

    quoted = ground_verdict(
        {
            "status": "Verified",
            "explanation": "The passage states it.",
            "supporting_excerpt": PASSAGE,
            "opposing_excerpt": "",
        },
        PASSAGE,
    )
    assert quoted["status"] == "Verified"


def test_claims_from_unknown_sources_are_removed():
    sources = [{"url": "https://example.edu/sleep"}]
    claims = filter_claims(
        [
            {"source_url": "https://example.edu/sleep", "text": "Sleep duration changed recall.", "kind": "fact"},
            {"source_url": "https://invented.example/nope", "text": "This source was never retrieved.", "kind": "fact"},
        ],
        sources,
        limit=8,
    )
    assert len(claims) == 1
    assert claims[0]["source_url"] == "https://example.edu/sleep"


def test_publication_dates_are_not_kept_as_contradictions():
    claims = [
        {"id": "a", "source_url": "https://example.edu/a", "kind": "statistic", "text": "Gain was 20 percent."},
        {"id": "b", "source_url": "https://example.edu/b", "kind": "statistic", "text": "Gain was 5 percent."},
    ]
    kept = filter_contradictions(
        [
            {
                "claim_id_a": "a",
                "claim_id_b": "b",
                "kind": "different_publication_date",
                "explanation": "The papers were published in different years.",
                "context": "",
            },
            {
                "claim_id_a": "a",
                "claim_id_b": "b",
                "kind": "conflicting_number_or_date",
                "explanation": "The reported recall gains are different.",
                "context": "Both compare seven hours with four hours.",
            },
        ],
        claims,
    )
    assert len(kept) == 1
    assert kept[0]["explanation"] == "The reported recall gains are different."


def test_report_drops_citations_that_were_not_retrieved():
    report = filter_report(
        {
            "summary": "A sourced note.",
            "findings": [
                {
                    "text": "Recall increased.",
                    "citation_urls": ["https://example.edu/sleep", "https://invented.example/extra"],
                    "certainty": "supported",
                }
            ],
            "uncertainties": [],
            "limitations": [],
        },
        [{"url": "https://example.edu/sleep"}],
        [{"status": "Verified", "source_url": "https://example.edu/sleep"}],
    )
    assert report["findings"][0]["citation_urls"] == ["https://example.edu/sleep"]


def test_tavily_payload_keeps_title_url_and_snippet():
    hits = hits_from_tavily(
        {
            "results": [
                {"title": "Sleep study", "url": "https://example.edu/sleep", "content": PASSAGE},
                {"title": "Missing url", "content": "ignored"},
            ]
        },
        "sleep and memory",
    )
    assert len(hits) == 1
    assert hits[0].url == "https://example.edu/sleep"
    assert hits[0].snippet == PASSAGE
    assert hits[0].query == "sleep and memory"


def test_html_text_skips_scripts():
    text = text_from_html("<html><style>body{}</style><p>Visible finding.</p><script>secret()</script></html>")
    assert text == "Visible finding."
    assert "secret" not in text
