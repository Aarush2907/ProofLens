from app.research.activity import emit
from app.research.checks import ground_verdict, passage_contains
from app.research.contracts import Verdict


SYSTEM = (
    "Check one claim against one source passage. "
    "Use Verified only when the passage directly states the claim. "
    "Use Partially supported when the passage supports only part of the claim. "
    "Use Contradicted when the passage conflicts with the claim. "
    "Otherwise use Insufficient evidence. "
    "supporting_excerpt and opposing_excerpt must be copied from the passage."
)


def check_claims(state: dict, model, retrieve_evidence=None, verify=None) -> dict:
    session_id = state.get("session_id") or ""
    emit("fact_checker_started", "Fact-checker started.", agent="fact_checker", session_id=session_id)
    sources = {source["url"]: source for source in state.get("sources") or []}
    verifications = []
    for claim in state.get("claims") or []:
        own = _passage(sources.get(claim["source_url"]))
        retrieved = []
        if retrieve_evidence is not None and session_id and claim.get("kind") != "opinion":
            retrieved = retrieve_evidence(claim["text"], session_id) or []
        passage = _combined(own, retrieved)
        if claim.get("kind") == "opinion":
            verdict = _opinion(claim["id"])
        elif len(passage.strip()) < 24:
            verdict = _missing_passage(claim["id"])
        else:
            raw = verify(claim["text"], passage) if verify is not None else model(Verdict, SYSTEM, _prompt(claim, passage)).model_dump()
            grounded = ground_verdict(raw, passage)
            grounded.update(_attribution(grounded, retrieved, claim))
            _note_memory(grounded, retrieved)
            verdict = {"claim_id": claim["id"], **grounded}
        verifications.append(verdict)
        emit(
            "claim_verified",
            f"Checked a claim: {verdict['status']}.",
            agent="fact_checker",
            detail={"claim_id": claim["id"], "status": verdict["status"]},
            session_id=session_id,
        )
    return {"verifications": verifications, "stage": "claims_checked"}


def _combined(own: str, retrieved: list[dict]) -> str:
    parts = [own] if own.strip() else []
    for item in retrieved:
        text = (item.get("text") or "").strip()
        if text and text not in own:
            parts.append(text)
    return "\n".join(parts)


def _attribution(verdict: dict, retrieved: list[dict], claim: dict) -> dict:
    extra = {}
    for stance, field in (("supporting", "supporting_excerpt"), ("opposing", "opposing_excerpt")):
        excerpt = verdict.get(field) or ""
        source_id, url = claim.get("source_id") or "", claim["source_url"]
        for item in retrieved:
            if excerpt and passage_contains(excerpt, item.get("text") or ""):
                source_id = item.get("source_id") or source_id
                url = item.get("url") or url
                break
        extra[f"{stance}_source_id"] = source_id
        extra[f"{stance}_url"] = url
    return extra


def _note_memory(verdict: dict, retrieved: list[dict]) -> None:
    notes = []
    if any(item.get("from_memory") for item in retrieved):
        notes.append("A passage from earlier research was included.")
    if any(item.get("possibly_outdated") for item in retrieved):
        notes.append("Some retrieved evidence is older than the freshness window and may be outdated.")
    if notes and verdict.get("explanation"):
        verdict["explanation"] = verdict["explanation"].rstrip() + " " + " ".join(notes)


def _passage(source: dict | None) -> str:
    if source is None:
        return ""
    return f"{source.get('snippet', '')}\n{source.get('content', '')}"


def _prompt(claim: dict, passage: str) -> str:
    return f"Claim: {claim['text']}\n\nPassage:\n{passage[:5000]}"


def _opinion(claim_id: str) -> dict:
    return {
        "claim_id": claim_id,
        "status": "Insufficient evidence",
        "explanation": "This was classified as an opinion, so it is not treated as a fact.",
        "supporting_excerpt": "",
        "opposing_excerpt": "",
    }


def _missing_passage(claim_id: str) -> dict:
    return {
        "claim_id": claim_id,
        "status": "Insufficient evidence",
        "explanation": "The source did not include a passage long enough to check this claim.",
        "supporting_excerpt": "",
        "opposing_excerpt": "",
    }
