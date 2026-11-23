import uuid
from datetime import datetime, timezone

from app.research.export import group_claims, render_markdown, render_pdf
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
    assert "| Status | In progress |" in markdown.text
    assert "attachment" in markdown.headers["content-disposition"]
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert "attachment" in pdf.headers["content-disposition"]


def test_findings_cite_numbered_sources_and_drop_uncollected_urls():
    session = _session(
        sources=[_source(SAVED)],
        report=ReportRead(
            summary="The trial reported a figure.",
            findings=[
                FindingRead(
                    text="Twenty percent slept under six hours.",
                    citation_urls=[SAVED, "https://example.edu/not-collected"],
                    certainty="supported",
                )
            ],
            uncertainties=["Only one trial was found."],
            limitations=["The sample is small."],
        ),
    )

    markdown = render_markdown(session)

    assert "1. Twenty percent slept under six hours." in markdown
    assert "Confidence: Supported by a verified claim. Sources: [1]." in markdown
    assert "not-collected" not in markdown
    assert "Only one trial was found." in markdown
    assert "The sample is small." in markdown
    assert "### [1] Trial report" in markdown


def test_export_groups_claims_with_quotations_and_separates_rejected_ones():
    session = _session(
        sources=[_source(SAVED), _source(OTHER, title="Audit")],
        claims=[
            _claim("Twenty percent slept under six hours.", SAVED, "Verified", "approved", "supporting"),
            _claim("Five percent slept under six hours.", OTHER, "Contradicted", "approved", "opposing"),
            _claim("Most adults sleep well.", SAVED, "Insufficient evidence", "approved"),
            _claim("Everyone sleeps eight hours.", SAVED, "Verified", "rejected", "supporting"),
        ],
        contradictions=[
            ContradictionRead(
                explanation="The figures conflict.",
                context="Different samples.",
                claim_text="Twenty percent slept under six hours.",
                other_claim_text="Five percent slept under six hours.",
                source_url=SAVED,
                other_source_url=OTHER,
            )
        ],
    )

    groups = group_claims(session.claims)
    markdown = render_markdown(session)

    assert [claim.text for claim in groups["Verified"]] == ["Twenty percent slept under six hours."]
    assert [claim.text for claim in groups["Rejected in review"]] == ["Everyone sleeps eight hours."]
    assert "| Verified | 1 |" in markdown
    assert "| Contradicted | 1 |" in markdown
    assert "| Partially supported | 0 |" in markdown
    assert "#### 1. Twenty percent slept under six hours." in markdown
    assert "Source: [1] Trial report" in markdown
    assert "Review: Approved" in markdown
    assert "> Supporting quotation: Quoted passage text here." in markdown
    assert "> Conflicting quotation: Quoted passage text here." in markdown
    rejected = markdown.split("### Rejected in review (1)")[1].split("## Where sources disagree")[0]
    assert "Everyone sleeps eight hours." in rejected
    verified = markdown.split("### Verified (1)")[1].split("### Contradicted")[0]
    assert "Everyone sleeps eight hours." not in verified
    assert "The figures conflict." in markdown
    assert "> Five percent slept under six hours. [2]" in markdown
    assert "A person reviewed the claims (3 approved, 1 rejected)." in markdown


def test_sources_list_their_details_for_the_reader():
    session = _session(sources=[_source(SAVED)])

    markdown = render_markdown(session)

    assert "| Source type | Primary-style source |" in markdown
    assert "| Author | Dr Rao |" in markdown
    assert "| Published | 2026-01-05 |" in markdown
    assert "| Found with search | sleep |" in markdown
    assert "## How to read this report" in markdown


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
            status=status,
            explanation="The passage says so.",
            supporting_excerpt="Quoted passage text here." if stance == "supporting" else "",
            opposing_excerpt="Quoted passage text here." if stance == "opposing" else "",
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
        author="Dr Rao",
        published_on="2026-01-05",
        quality=SourceQualityRead(
            role="primary",
            publisher="",
            author_known=True,
            date_known=True,
            specific=True,
            reports_original_data=True,
            reasons=["The page names an author and a date."],
        ),
    )
