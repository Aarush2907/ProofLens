from app.research import pages
from app.research.agents.researcher import collect_sources
from app.research.checks import filter_report
from app.research.contracts import SearchHit, SearchQueryPlan
from app.research.pages import is_block_page
from app.research.quality import assess_source

CLOUDFLARE = "Your Ray ID for this request is a5d1e9fadf0062af. Troubleshooting Cloudflare Error."
ARTICLE = "Applications sent in the morning are reviewed first. " * 40


def test_challenge_pages_are_recognised_but_a_long_article_that_mentions_one_is_not():
    assert is_block_page(CLOUDFLARE) is True
    assert is_block_page("One moment, please... Loader Please wait while your request is being verified") is True
    assert is_block_page("Please wait.", title="Just a moment...") is True
    assert is_block_page(ARTICLE + " Some sites show a captcha or say just a moment.") is False


def test_a_fetched_challenge_page_is_not_returned_as_page_text(monkeypatch):
    html = "<html><head><title>Just a moment...</title></head><body>Checking your browser</body></html>"
    monkeypatch.setattr(pages, "_download", lambda url: (html, "text/html"))

    assert pages.fetch_page_text("https://example.edu/a", 1000) == ""


def _hit(url: str, title: str, text: str) -> SearchHit:
    return SearchHit(title=title, url=url, snippet=text, content=text, query="q", published_on="", author="")


def test_the_researcher_skips_a_blocked_result_and_says_when_it_used_only_the_snippet():
    hits = [
        _hit("https://blocked.example.com/a", "Just a moment...", CLOUDFLARE),
        _hit("https://news.example.org/b", "Morning applications", ARTICLE[:600]),
    ]
    state = {"question": "Is morning better?", "session_id": ""}

    result = collect_sources(
        state,
        lambda schema, system, user: SearchQueryPlan(queries=["morning applications"]),
        lambda query, limit: hits,
        lambda url, limit: "",
    )

    assert [source["url"] for source in result["sources"]] == ["https://news.example.org/b"]
    source = result["sources"][0]
    assert source["content"] == source["snippet"]
    quality = assess_source({**source, "domain": "news.example.org"})
    assert "Only the search-result snippet was available, not the full page." in quality["reasons"]


def test_a_source_with_fetched_text_is_not_marked_snippet_only():
    source = {
        "url": "https://news.example.org/b",
        "title": "Morning applications",
        "snippet": "Short snippet.",
        "content": ARTICLE,
        "domain": "news.example.org",
    }

    assert "Only the search-result snippet was available, not the full page." not in assess_source(source)["reasons"]


def test_a_partly_supported_finding_needs_a_claim_that_is_at_least_partly_supported():
    sources = [
        {"url": "https://a.example.org/x", "title": "A"},
        {"url": "https://b.example.org/y", "title": "B"},
    ]
    verifications = [
        {"source_url": "https://a.example.org/x", "status": "Insufficient evidence"},
        {"source_url": "https://b.example.org/y", "status": "Partially supported"},
    ]
    report = {
        "summary": "s",
        "findings": [
            {"text": "From A.", "citation_urls": ["https://a.example.org/x"], "certainty": "partial"},
            {"text": "From B.", "citation_urls": ["https://b.example.org/y"], "certainty": "partial"},
        ],
    }

    kept = filter_report(report, sources, verifications)["findings"]

    assert [(item["text"], item["certainty"]) for item in kept] == [
        ("From A.", "uncertain"),
        ("From B.", "partial"),
    ]
