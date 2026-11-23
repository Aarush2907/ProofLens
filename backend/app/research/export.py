"""Markdown and PDF exports built only from a saved research session.

Citation URLs that are not among the saved sources are left out. The export
can be downloaded before the writer finishes, and it says so.
"""

from app.research.checks import canonical_url
from app.schemas.research import ResearchSessionRead

CLAIM_GROUPS = (
    ("Verified", "verified"),
    ("Partially supported", "partial"),
    ("Contradicted", "contradicted"),
    ("Insufficient evidence", "insufficient"),
)


def render_markdown(session: ResearchSessionRead) -> str:
    lines = ["# ProofLens research report", ""]
    for title, body in build_sections(build_document(session)):
        lines.append(f"## {title}")
        lines.append("")
        lines.extend(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_pdf(session: ResearchSessionRead) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    _write(pdf, 16, 8, "ProofLens research report")
    pdf.ln(2)
    for title, body in build_sections(build_document(session)):
        _write(pdf, 12, 7, title)
        _write(pdf, 10, 5, "\n".join(body))
        pdf.ln(2)
    return bytes(pdf.output())


def build_sections(document: dict) -> list[tuple[str, list[str]]]:
    return [
        ("Research question", [document["question"]]),
        ("Executive summary", [document["summary"]]),
        ("Methodology", [document["methodology"]]),
        ("Important findings", _findings(document["findings"])),
        ("Verified claims", _claims(document["verified"])),
        ("Partially supported claims", _claims(document["partial"])),
        ("Contradicted claims", _claims(document["contradicted"])),
        ("Insufficient evidence", _claims(document["insufficient"])),
        ("Rejected in review", _claims(document["rejected"])),
        ("Supporting sources", _or_none(document["supporting_sources"])),
        ("Opposing sources", _or_none(document["opposing_sources"])),
        ("Contradiction summary", document["contradictions"] or ["No contradiction was saved."]),
        ("Limitations", document["limitations"]),
        ("Source bibliography", document["bibliography"] or ["No source was saved."]),
    ]


def build_document(session: ResearchSessionRead) -> dict:
    known = {canonical_url(source.url): source for source in session.sources if canonical_url(source.url)}
    groups: dict[str, list[dict]] = {key: [] for _status, key in CLAIM_GROUPS}
    groups["rejected"] = []
    supporting: set[str] = set()
    opposing: set[str] = set()
    status_keys = dict(CLAIM_GROUPS)
    for claim in session.claims:
        entry = {"text": claim.text, "url": claim.source_url}
        if claim.review_status == "rejected":
            groups["rejected"].append(entry)
            continue
        status = claim.verification.status if claim.verification else "Insufficient evidence"
        groups[status_keys.get(status, "insufficient")].append(entry)
        for item in claim.evidence:
            url = canonical_url(item.source_url)
            if url not in known:
                continue
            (supporting if item.stance == "supporting" else opposing).add(url)

    summary = "The writer has not finished a report for this run. The sections below are the evidence saved so far."
    limitations = [
        "A passage check shows whether the collected text supports the claim. It does not prove the claim is true outside that text.",
    ]
    findings = []
    if session.report is not None:
        summary = session.report.summary or summary
        limitations.extend(session.report.limitations)
        findings = [
            {
                "text": finding.text,
                "certainty": finding.certainty,
                "citation_urls": [
                    known[canonical_url(url)].url for url in finding.citation_urls if canonical_url(url) in known
                ],
            }
            for finding in session.report.findings
        ]

    return {
        "question": session.question,
        "summary": summary,
        "methodology": describe_method(session),
        "findings": findings,
        **groups,
        "supporting_sources": [_source_line(known[url]) for url in sorted(supporting)],
        "opposing_sources": [_source_line(known[url]) for url in sorted(opposing)],
        "contradictions": [
            f"{item.claim_text} ({item.source_url}) disagrees with {item.other_claim_text} "
            f"({item.other_source_url}). {item.explanation}"
            for item in session.contradictions
        ],
        "limitations": limitations,
        "bibliography": [_source_line(source) for source in session.sources],
    }


def describe_method(session: ResearchSessionRead) -> str:
    """Describe only the steps that left saved results."""

    steps = []
    if session.sources:
        steps.append(f"ProofLens collected {len(session.sources)} source(s) and stored their text.")
    else:
        steps.append("No source was collected for this run.")
    if session.claims:
        steps.append(
            f"It extracted {len(session.claims)} claim(s) and checked each against the retrieved passages. "
            "A quotation was kept only when it appeared in the passage."
        )
    if session.contradictions:
        steps.append("Disagreements between sources were recorded separately.")

    approved = sum(1 for claim in session.claims if claim.review_status == "approved")
    rejected = sum(1 for claim in session.claims if claim.review_status == "rejected")
    if approved or rejected:
        steps.append(f"A person reviewed the claims ({approved} approved, {rejected} rejected).")
    elif session.stage == "awaiting_review":
        steps.append("The claims are waiting for review.")
    elif session.claims:
        steps.append("No review decision was saved.")
    if session.status == "failed" and session.error_message:
        steps.append(f"The run stopped: {session.error_message}")
    steps.append("This export lists what was saved. It does not add sources that were not collected.")
    return " ".join(steps)


def _findings(findings: list[dict]) -> list[str]:
    if not findings:
        return ["No finding with a saved citation was available."]
    lines = []
    for finding in findings:
        cites = ", ".join(finding["citation_urls"]) or "no saved citation"
        lines.append(f"- {finding['text']} ({finding['certainty']}; {cites})")
    return lines


def _claims(claims: list[dict]) -> list[str]:
    if not claims:
        return ["None saved."]
    return [f"- {claim['text']} ({claim['url']})" for claim in claims]


def _or_none(lines: list[str]) -> list[str]:
    return lines or ["None saved."]


def _source_line(source) -> str:
    return f"{source.title or source.url} - {source.url}"


def _write(pdf, size: int, line_height: int, text: str) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", size=size)
    # Core fonts are Latin-1 only. Other characters become "?" instead of failing.
    safe = text.encode("latin-1", "replace").decode("latin-1")
    pdf.multi_cell(0, line_height, safe, new_x="LMARGIN", new_y="NEXT")
