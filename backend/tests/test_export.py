import uuid
from datetime import datetime, timezone

from app.research.export import build_document, render_markdown, render_pdf
from app.schemas.research import (
    ClaimRead,
    ContradictionRead,
    EvidenceRead,
    FindingRead,
    ReportRead,
    ResearchSessionRead,
    SourceQualityRead,
    SourceRead,
    VerificationRead,
)


QUESTION = "What share of adults in the trial slept under six hours?"
SAVED = "https://example.edu/sleep"
OTHER = "https://example.org/audit"
LONG_URL = "https://example.edu/" + "a" * 160


def test_export_endpoints_work_before_a_report_exists(client):
    created = client.post("/api/research", json={"question": QUESTION}).json()

    markdown = client.get(f"/api/research/{created['id']}/export.md")
    pdf = client.get(f"/api/research/{created['id']}/export.pdf")

    assert markdown.status_code == 200
    assert "text/markdown" in markdown.headers["content-type"]
    assert QUESTION in markdown.text
    assert "has not finished" in markdown.text
    assert "No source was collected" in markdown.text
    assert "A person reviewed" not in markdown.text
    assert "attachment" in markdown.headers["content-disposition"]
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert "attachment" in pdf.headers["content-disposition"]


def test_export_drops_a_citation_that_was_not_collected():
    session = _session(
        sources=[_source(SAVED)],
        report=ReportRead(
            summary="The trial reported a figure.",
            findings=[
                FindingRead(
                    text="Twenty percent slept under six hours.",
                    citation_urls=[SAVED, "https://example.edu/not-collected"],
                    certainty="grounded",
                )
            ],
            uncertainties=[],
            limitations=["The sample is small."],
        ),
    )

    document = build_document(session)
    markdown = render_markdown(session)

    assert document["findings"][0]["citation_urls"] == [SAVED]
    assert "not-collected" not in markdown
    assert "The sample is small." in markdown


def test_export_groups_claims_and_leaves_rejected_ones_out_of_the_findings():
    session = _session(
        sources=[_source(SAVED), _source(OTHER)],
        claims=[
            _claim("Twenty percent slept under six hours.", SAVED, "Verified", "approved", "supporting"),
            _claim("Five percent slept under six hours.", OTHER, "Contradicted", "approved", "opposing"),
            _claim("Most adults sleep well.", SAVED, "Insufficient evidence", "approved"),
            _claim("Everyone sleeps eight hours.", SAVED, "Verified", "rejected", "supporting"),
        ],
        contradictions=[
            ContradictionRead(
                explanation="The figures conflict.",
                context="",
                claim_text="Twenty percent slept under six hours.",
                other_claim_text="Five percent slept under six hours.",
                source_url=SAVED,
                other_source_url=OTHER,
            )
        ],
    )

    document = build_document(session)
    markdown = render_markdown(session)

    assert [item["text"] for item in document["verified"]] == ["Twenty percent slept under six hours."]
    assert [item["text"] for item in document["contradicted"]] == ["Five percent slept under six hours."]
    assert [item["text"] for item in document["insufficient"]] == ["Most adults sleep well."]
    assert [item["text"] for item in document["rejected"]] == ["Everyone sleeps eight hours."]
    assert document["supporting_sources"] == ["Trial report - " + SAVED]
    assert document["opposing_sources"] == ["Trial report - " + OTHER]
    verified_section = markdown.split("## Verified claims")[1].split("## Partially")[0]
    assert "Everyone sleeps eight hours." not in verified_section
    assert "The figures conflict." in markdown
    assert "(3 approved, 1 rejected)" in markdown


def test_pdf_handles_long_urls_and_text_outside_latin_1():
    session = _session(
        sources=[_source(LONG_URL, title="Étude sur le sommeil — résumé")],
        claims=[_claim("Les adultes dorment peu \u2192 vrai.", LONG_URL, "Verified", "approved", "supporting")],
    )

    assert render_pdf(session).startswith(b"%PDF")


def _session(sources, report=None, claims=None, contradictions=None) -> ResearchSessionRead:
    now = datetime.now(timezone.utc)
    return ResearchSessionRead(
        id=uuid.uuid4(),
        question=QUESTION,
        status="completed" if report else "running",
        stage="completed" if report else "awaiting_review",
        created_at=now,
        updated_at=now,
        sources=sources,
        claims=claims or [],
        contradictions=contradictions or [],
        report=report,
    )


def _claim(text, url, status, review, stance=None) -> ClaimRead:
    evidence = []
    if stance:
        evidence.append(EvidenceRead(id=uuid.uuid4(), source_url=url, stance=stance, passage="Quoted passage text here."))
    return ClaimRead(
        id=uuid.uuid4(),
        source_url=url,
        text=text,
        kind="statistic",
        review_status=review,
        verification=VerificationRead(
            status=status, explanation="", supporting_excerpt="", opposing_excerpt=""
        ),
        evidence=evidence,
    )


def _source(url: str, title: str = "Trial report") -> SourceRead:
    return SourceRead(
        id=uuid.uuid4(),
        url=url,
        title=title,
        domain="example.edu",
        snippet="",
        content="",
        search_query="sleep",
        quality=SourceQualityRead(
            role="unclear",
            publisher="",
            author_known=False,
            date_known=False,
            specific=False,
            reports_original_data=False,
            reasons=[],
        ),
    )
