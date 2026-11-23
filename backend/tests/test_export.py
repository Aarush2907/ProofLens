import uuid
from datetime import datetime, timezone

from app.research.export import build_document, render_markdown, render_pdf
from app.schemas.research import (
    FindingRead,
    ReportRead,
    ResearchSessionRead,
    SourceQualityRead,
    SourceRead,
)


QUESTION = "What share of adults in the trial slept under six hours?"


def test_export_endpoints_work_before_a_report_exists(client):
    created = client.post("/api/research", json={"question": QUESTION}).json()

    markdown = client.get(f"/api/research/{created['id']}/export.md")
    pdf = client.get(f"/api/research/{created['id']}/export.pdf")

    assert markdown.status_code == 200
    assert "text/markdown" in markdown.headers["content-type"]
    assert QUESTION in markdown.text
    assert "has not finished" in markdown.text
    assert "attachment" in markdown.headers["content-disposition"]
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert "attachment" in pdf.headers["content-disposition"]


def test_export_drops_a_citation_that_was_not_collected():
    saved = "https://example.edu/sleep"
    session = _session(
        sources=[_source(saved)],
        report=ReportRead(
            summary="The trial reported a figure.",
            findings=[
                FindingRead(
                    text="Twenty percent slept under six hours.",
                    citation_urls=[saved, "https://example.edu/not-collected"],
                    certainty="grounded",
                )
            ],
            uncertainties=[],
            limitations=["The sample is small."],
        ),
    )

    document = build_document(session)
    markdown = render_markdown(session)

    assert document["findings"][0]["citation_urls"] == [saved]
    assert "not-collected" not in markdown
    assert saved in markdown
    assert "The sample is small." in markdown
    assert render_pdf(session).startswith(b"%PDF")


def _session(sources, report) -> ResearchSessionRead:
    now = datetime.now(timezone.utc)
    return ResearchSessionRead(
        id=uuid.uuid4(),
        question=QUESTION,
        status="completed",
        stage="completed",
        created_at=now,
        updated_at=now,
        sources=sources,
        claims=[],
        contradictions=[],
        report=report,
    )


def _source(url: str) -> SourceRead:
    return SourceRead(
        id=uuid.uuid4(),
        url=url,
        title="Trial report",
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
