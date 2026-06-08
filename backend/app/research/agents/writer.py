from app.research.activity import emit
from app.research.checks import filter_report
from app.research.contracts import ReportDraft


SYSTEM = (
    "Write a research note using only the claims, verdicts, disagreements, and sources below. "
    "Every finding must cite source URLs from the source list. "
    "Do not present an unverified claim as established. "
    "Explain what is uncertain and what the collected material cannot show. "
    "Do not add facts that are not in the input."
)


def write_report(state: dict, model) -> dict:
    session_id = state.get("session_id") or ""
    emit("writer_started", "Writer started.", agent="writer", session_id=session_id)
    draft = model(ReportDraft, SYSTEM, _packet(state))
    report = filter_report(draft.model_dump(), state.get("sources") or [], _annotated(state))
    if not report["summary"]:
        report["summary"] = _fallback_summary(state)
    rejected = [
        claim for claim in state.get("claims") or [] if claim.get("review_status") == "rejected"
    ]
    if rejected:
        report["limitations"] = list(report["limitations"]) + [
            f"{len(rejected)} claim(s) were rejected in review and were left out of the findings."
        ]
    emit("report_completed", "Report completed.", agent="writer", session_id=session_id, terminal=True)
    return {"report": report, "stage": "report_written"}


def _annotated(state: dict) -> list[dict]:
    claims = {claim["id"]: claim for claim in state.get("claims") or []}
    annotated = []
    for verdict in state.get("verifications") or []:
        claim = claims.get(verdict.get("claim_id"))
        if claim is None or claim.get("review_status") == "rejected":
            continue
        annotated.append({**verdict, "source_url": claim["source_url"]})
    return annotated


def _packet(state: dict) -> str:
    lines = [f"Question: {state['question']}", "", "Sources:"]
    for source in state.get("sources") or []:
        lines.append(f"- {source.get('title', '')} | {source['url']}")
    lines.append("")
    lines.append("Claims:")
    verdicts = {item["claim_id"]: item for item in state.get("verifications") or []}
    if not state.get("claims"):
        lines.append("None.")
    for claim in state.get("claims") or []:
        if claim.get("review_status") == "rejected":
            continue
        verdict = verdicts.get(claim["id"], {})
        lines.append(
            f"- {claim['text']} | {claim['kind']} | {claim['source_url']} | {verdict.get('status', 'unchecked')}"
        )
    lines.append("")
    lines.append("Disagreements:")
    if not state.get("contradictions"):
        lines.append("None.")
    for item in state.get("contradictions") or []:
        lines.append(f"- {item['explanation']} Context: {item.get('context', '')}")
    return "\n".join(lines)[:12000]


def _fallback_summary(state: dict) -> str:
    if not state.get("sources"):
        return "No sources were collected, so this question does not have a sourced finding."
    return "The collected material did not produce a sourced summary."
