def evidence_for(claims: list[dict], verifications: list[dict]) -> list[dict]:
    """Turn grounded excerpts into evidence rows tied to a claim and a source.

    An empty excerpt is not evidence. The passage stored here is the same
    text the fact-checker had to find inside the source.
    """

    claims_by_id = {claim["id"]: claim for claim in claims}
    rows = []
    for verdict in verifications:
        claim = claims_by_id.get(verdict.get("claim_id"))
        if claim is None:
            continue
        for stance, field in (("supporting", "supporting_excerpt"), ("opposing", "opposing_excerpt")):
            passage = (verdict.get(field) or "").strip()
            if not passage:
                continue
            rows.append(
                {
                    "claim_id": claim["id"],
                    "source_id": claim.get("source_id") or "",
                    "source_url": claim["source_url"],
                    "stance": stance,
                    "passage": passage,
                }
            )
    return rows
