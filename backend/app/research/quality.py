from urllib.parse import urlsplit

# Phrases that describe a page reporting its own measurement.
# A news article that merely quotes a study will not match these.
ORIGINAL_DATA_PHRASES = (
    "we measured",
    "we collected",
    "our results",
    "our study",
    "this dataset",
    "methods:",
)


def domain_of(url: str) -> str:
    host = urlsplit(url or "").netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host.split(":")[0]


def _academic(domain: str) -> bool:
    return (
        domain.endswith(".edu")
        or domain.endswith(".gov")
        or domain.endswith(".ac.uk")
        or ".gov." in f".{domain}."
    )


def assess_source(source: dict) -> dict:
    """Describe what the saved source record actually contains.

    This is not a reliability score. A government domain and a named author
    do not prove that a claim is true. Verification stays on the claim.
    """

    domain = (source.get("domain") or domain_of(source.get("url") or "")).strip()
    author = (source.get("author") or "").strip()
    published = (source.get("published_on") or "").strip()
    passage = source.get("content") or source.get("snippet") or ""
    text = f"{source.get('title') or ''}\n{passage}".lower()
    publisher = domain or "Unknown publisher"
    reasons = []
    if domain:
        reasons.append(f"Publisher is identified from the domain: {publisher}.")
    else:
        reasons.append("No domain could be read from the URL.")
    if author:
        reasons.append(f"An author or organisation was retrieved: {author}.")
    else:
        reasons.append("No author or organisation was retrieved with this source.")
    if published:
        reasons.append(f"A publication date was retrieved: {published}.")
    else:
        reasons.append("No publication date was retrieved, so recency cannot be judged from this record.")
    specific = len(passage.split()) >= 40
    if specific:
        reasons.append("The retrieved text is long enough to quote a specific passage.")
    else:
        reasons.append("The retrieved text is short, so the evidence is not specific.")

    reports_original_data = any(phrase in text for phrase in ORIGINAL_DATA_PHRASES)
    academic = _academic(domain)
    if reports_original_data:
        reasons.append("The text describes the page's own measurement or dataset.")
    else:
        reasons.append("The text does not show that this page contains the original data.")
    if academic:
        reasons.append("The domain belongs to an academic or government host.")
    else:
        reasons.append("The domain is not an academic or government host.")

    if academic and reports_original_data:
        role = "primary"
        reasons.append("Those two signals together are why this is labelled a primary-style source.")
    elif academic or reports_original_data:
        role = "unclear"
        reasons.append("Only one primary-source signal is present, so the role stays unclear.")
    else:
        role = "secondary"
        reasons.append("Nothing retrieved shows this page is the original data, so it is treated as secondary or unidentified.")
    reasons.append("This source record is separate from whether a particular claim is verified.")
    return {
        "role": role,
        "publisher": publisher,
        "author_known": bool(author),
        "date_known": bool(published),
        "specific": specific,
        "reports_original_data": reports_original_data,
        "reasons": reasons,
    }
