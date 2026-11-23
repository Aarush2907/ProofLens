"""Markdown and PDF exports built only from a saved research session.

Citation URLs that are not among the saved sources are left out. The export
can be downloaded before the writer finishes, and it says so.
"""

from app.research.checks import canonical_url
from app.schemas.research import ResearchSessionRead

_METHOD = (
    "ProofLens searched for sources, stored the retrieved passages, extracted claims, "
    "and checked each claim against those passages. A quotation was kept only when it "
    "appeared in the passage. Disagreements between sources were recorded separately. "
    "A person reviewed the claims before the report was written. "
    "This export lists what was saved. It does not add sources that were not collected."
)


def render_markdown(session: ResearchSessionRead) -> str:
    document = build_document(session)
    lines = ["# ProofLens research report", ""]
    sections = [
        ("Research question", [document["question"]]),
        ("Executive summary", [document["summary"]]),
        ("Methodology", [document["methodology"]]),
        ("Important findings", _findings(document["findings"])),
        ("Verified claims", _claims(document["verified"])),
        ("Partially supported claims", _claims(document["partial"])),
        ("Contradicted claims", _claims(document["contradicted"])),
        ("Insufficient evidence", _claims(document["insufficient"])),
        ("Supporting sources", _sources(document["supporting_sources"])),
        ("Opposing sources", _sources(document["opposing_sources"])),
        ("Contradiction summary", document["contradictions"] or ["No contradiction was saved."]),
        ("Limitations", document["limitations"]),
        ("Source bibliography", _bibliography(document["bibliography"])),
    ]
    for title, body in sections:
        lines.append(f"## {title}")
        lines.append("")
        lines.extend(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_pdf(session: ResearchSessionRead) -> bytes:
    from fpdf import FPDF

    document = build_document(session)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_font("Helvetica", size=16)
    pdf.multi_cell(0, 8, _pdf_text("ProofLens research report"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    blocks = [
        ("Research question", document["question"]),
        ("Executive summary", document["summary"]),
        ("Methodology", document["methodology"]),
        ("Important findings", "\n".join(_findings(document["findings"]))),
        ("Verified claims", "\n".join(_claims(document["verified"]))),
        ("Partially supported claims", "\n".join(_claims(document["partial"]))),
        ("Contradicted claims", "\n".join(_claims(document["contradicted"]))),
        ("Insufficient evidence", "\n".join(_claims(document["insufficient"]))),
        ("Supporting sources", "\n".join(_sources(document["supporting_sources"]))),
        ("Opposing sources", "\n".join(_sources(document["opposing_sources"]))),
        ("Contradiction summary", "\n".join(document["contradictions"] or ["No contradiction was saved."])),
        ("Limitations", "\n".join(document["limitations"])),
        ("Source bibliography", "\n".join(_bibliography(document["bibliography"]))),
    ]
    for title, body in blocks:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 7, _pdf_text(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 5, _pdf_text(body or "None saved."), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    return bytes(pdf.output())


def build_document(session: ResearchSessionRead) -> dict:
    known = {canonical_url(source.url): source for source in session.sources if canonical_url(source.url)}
    grouped = {
        "Verified": [],
        "Partially supported": [],
        "Contradicted": [],
        "Insufficient evidence": [],
    }
    supporting = set()
    opposing = set()
    for claim in session.claims:
        status = claim.verification.status if claim.verification else "Insufficient evidence"
        grouped.setdefault(status, []).append(
            {"text": claim.text, "url": claim.source_url, "kind": claim.kind}
        )
        for item in claim.evidence:
            url = canonical_url(item.source_url)
            if url not in known:
                continue
            if item.stance == "supporting":
                supporting.add(url)
            elif item.stance == "opposing":
                opposing.add(url)

    findings = []
    limitations = [
        "A passage check shows whether the collected text supports the claim. It does not prove the claim is true outside that text.",
    ]
    summary = (
        "The writer has not finished a report for this run. The sections below are the evidence saved so far."
    )
    if session.report is not None:
        summary = session.report.summary or summary
        limitations.extend(session.report.limitations)
        for finding in session.report.findings:
            urls = []
            for url in finding.citation_urls:
                canonical = canonical_url(url)
                if canonical in known:
                    urls.append(known[canonical].url)
            findings.append({"text": finding.text, "certainty": finding.certainty, "citation_urls": urls})

    contradictions = [
        f"{item.claim_text} ({item.source_url}) disagrees with {item.other_claim_text} ({item.other_source_url}). {item.explanation}"
        for item in session.contradictions
    ]
    return {
        "question": session.question,
        "summary": summary,
        "methodology": _METHOD,
        "findings": findings,
        "verified": grouped["Verified"],
        "partial": grouped["Partially supported"],
        "contradicted": grouped["Contradicted"],
        "insufficient": grouped["Insufficient evidence"],
        "supporting_sources": [_source_line(known[url]) for url in sorted(supporting)],
        "opposing_sources": [_source_line(known[url]) for url in sorted(opposing)],
        "contradictions": contradictions,
        "limitations": limitations,
        "bibliography": [_source_line(source) for source in session.sources],
    }


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


def _sources(lines: list[str]) -> list[str]:
    return lines or ["None saved."]


def _bibliography(lines: list[str]) -> list[str]:
    return lines or ["No source was saved."]


def _source_line(source) -> str:
    title = source.title or source.url
    return f"{title} — {source.url}"


def _pdf_text(value: str) -> str:
    return value.encode("latin-1", "replace").decode("latin-1")
