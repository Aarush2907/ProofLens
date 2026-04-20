import logging
from html.parser import HTMLParser

import httpx

logger = logging.getLogger(__name__)

MAX_PAGE_BYTES = 400_000


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def text_from_html(raw: str) -> str:
    parser = PageText()
    parser.feed(raw)
    return " ".join(" ".join(parser.parts).split())


def fetch_page_text(url: str, limit: int) -> str:
    try:
        with httpx.stream(
            "GET",
            url,
            timeout=8,
            follow_redirects=True,
            headers={"User-Agent": "ProofLens research desk"},
        ) as response:
            if response.status_code != 200:
                return ""
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text/plain" not in content_type:
                return ""
            chunks = []
            total = 0
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                total += len(chunk)
                if total >= MAX_PAGE_BYTES:
                    break
    except httpx.HTTPError as exc:
        logger.warning("Could not retrieve a source page: %s", exc.__class__.__name__)
        return ""

    raw = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
    if "html" in content_type:
        text = text_from_html(raw)
    else:
        text = " ".join(raw.split())
    return text[:limit]
