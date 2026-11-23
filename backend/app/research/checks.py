import re
from urllib.parse import urlsplit, urlunsplit

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")

KEPT_DISAGREEMENTS = {"factual_disagreement", "conflicting_number_or_date"}
GROUNDED_STATUSES = {"Verified", "Partially supported"}
STATUS_NAMES = {
    "verified": "Verified",
    "partially supported": "Partially supported",
    "contradicted": "Contradicted",
    "insufficient evidence": "Insufficient evidence",
}


def canonical_url(url: str) -> str:
    parsed = urlsplit((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.lower(), host, path, parsed.query, ""))


def collapsed(value: str) -> str:
    return " ".join(value.split()).lower()


def passage_contains(excerpt: str, passage: str) -> bool:
    excerpt_text = collapsed(excerpt)
    if len(excerpt_text) < 24:
        return False
    return excerpt_text in collapsed(passage)


def normalise_status(status: str) -> str:
    return STATUS_NAMES.get(status.strip().lower(), "Insufficient evidence")


def numbers_in(text: str) -> set[str]:
    return {number.replace(",", "") for number in _NUMBER.findall(text or "")}


def statistic_is_backed(claim_text: str, excerpt: str) -> bool:
    """Every number in a statistic claim must appear in the quoted excerpt."""

    claimed = numbers_in(claim_text)
    return bool(claimed) and claimed <= numbers_in(excerpt)


def ground_verdict(verdict: dict, passage: str, claim_text: str = "", claim_kind: str = "") -> dict:
    """Downgrade a verdict whose quotation is not in the retrieved passage.

    For a statistic claim, a supporting quotation must also contain the
    claim's numbers. A true sentence about a different figure is not support.
    """

    status = normalise_status(verdict.get("status", ""))
    supporting = verdict.get("supporting_excerpt") or ""
    opposing = verdict.get("opposing_excerpt") or ""
    grounded = dict(verdict)
    grounded["status"] = status

    if status in GROUNDED_STATUSES and not passage_contains(supporting, passage):
        return {
            **grounded,
            "status": "Insufficient evidence",
            "explanation": "The checker did not quote a passage that appears in the retrieved source.",
            "supporting_excerpt": "",
            "opposing_excerpt": "",
        }
    if (
        status in GROUNDED_STATUSES
        and claim_kind == "statistic"
        and not statistic_is_backed(claim_text, supporting)
    ):
        return {
            **grounded,
            "status": "Insufficient evidence",
            "explanation": "The quoted passage does not contain the figure stated in the claim.",
            "supporting_excerpt": "",
            "opposing_excerpt": "",
        }
    if status == "Contradicted" and not passage_contains(opposing, passage):
        return {
            **grounded,
            "status": "Insufficient evidence",
            "explanation": "The checker did not quote a conflicting passage from the retrieved source.",
            "supporting_excerpt": "",
            "opposing_excerpt": "",
        }
    return grounded


def known_source_urls(sources: list[dict]) -> set[str]:
    return {url for source in sources if (url := canonical_url(source.get("url", "")))}


def filter_claims(claims: list[dict], sources: list[dict], limit: int) -> list[dict]:
    allowed = known_source_urls(sources)
    kept = []
    for claim in claims:
        url = canonical_url(claim.get("source_url", ""))
        text = " ".join((claim.get("text") or "").split())
        if not url or url not in allowed or len(text) < 12:
            continue
        kept.append({**claim, "source_url": url, "text": text})
    factual = [claim for claim in kept if claim.get("kind") != "opinion"]
    opinions = [claim for claim in kept if claim.get("kind") == "opinion"]
    return (factual + opinions)[:limit]


def filter_contradictions(items: list[dict], claims: list[dict]) -> list[dict]:
    by_id = {claim["id"]: claim for claim in claims}
    kept = []
    seen = set()
    for item in items:
        if item.get("kind") not in KEPT_DISAGREEMENTS:
            continue
        first = by_id.get(item.get("claim_id_a"))
        second = by_id.get(item.get("claim_id_b"))
        if first is None or second is None:
            continue
        if first["source_url"] == second["source_url"]:
            continue
        if first.get("kind") == "opinion" or second.get("kind") == "opinion":
            continue
        pair = tuple(sorted((first["id"], second["id"])))
        if pair in seen:
            continue
        seen.add(pair)
        kept.append(
            {
                "claim_id": first["id"],
                "other_claim_id": second["id"],
                "explanation": (item.get("explanation") or "").strip(),
                "context": (item.get("context") or "").strip(),
            }
        )
    return [item for item in kept if item["explanation"]]


def filter_report(report: dict, sources: list[dict], verifications: list[dict]) -> dict:
    allowed = known_source_urls(sources)
    verified_urls = {
        canonical_url(item.get("source_url", ""))
        for item in verifications
        if item.get("status") == "Verified"
    }
    backed_urls = verified_urls | {
        canonical_url(item.get("source_url", ""))
        for item in verifications
        if item.get("status") == "Partially supported"
    }
    findings = []
    limitations = [item.strip() for item in report.get("limitations") or [] if item and item.strip()]
    for finding in report.get("findings") or []:
        text = (finding.get("text") or "").strip()
        if not text:
            continue
        citations = []
        for url in finding.get("citation_urls") or []:
            canonical = canonical_url(url)
            if canonical in allowed and canonical not in citations:
                citations.append(canonical)
        if not citations:
            limitations.append(f"Left out of the findings because it had no collected source: {text}")
            continue
        certainty = finding.get("certainty") or "uncertain"
        if certainty == "supported" and not any(url in verified_urls for url in citations):
            certainty = "uncertain"
        if certainty == "partial" and not any(url in backed_urls for url in citations):
            certainty = "uncertain"
        findings.append({"text": text, "citation_urls": citations, "certainty": certainty})

    uncertainties = [item.strip() for item in report.get("uncertainties") or [] if item and item.strip()]
    if not any(item.get("status") == "Verified" for item in verifications):
        uncertainties.append("No claim was verified against a retrieved passage.")

    return {
        "summary": (report.get("summary") or "").strip(),
        "findings": findings[:8],
        "uncertainties": list(dict.fromkeys(uncertainties)),
        "limitations": list(dict.fromkeys(limitations)),
    }
