from app.research.checks import ground_verdict
from app.research.contracts import Verdict


SYSTEM = (
    "Check one claim against one source passage. "
    "Use Verified only when the passage directly states the claim. "
    "Use Partially supported when the passage supports only part of the claim. "
    "Use Contradicted when the passage conflicts with the claim. "
    "Otherwise use Insufficient evidence. "
    "supporting_excerpt and opposing_excerpt must be copied from the passage."
)


def check_claims(state: dict, model) -> dict:
    sources = {source["url"]: source for source in state.get("sources") or []}
    verifications = []
    for claim in state.get("claims") or []:
        passage = _passage(sources.get(claim["source_url"]))
        if claim.get("kind") == "opinion":
            verifications.append(_opinion(claim["id"]))
            continue
        if len(passage.strip()) < 24:
            verifications.append(_missing_passage(claim["id"]))
            continue
        verdict = model(Verdict, SYSTEM, _prompt(claim, passage))
        grounded = ground_verdict(verdict.model_dump(), passage)
        verifications.append({"claim_id": claim["id"], **grounded})
    return {"verifications": verifications, "stage": "claims_checked"}


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
