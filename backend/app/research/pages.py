import logging
from html.parser import HTMLParser

import httpx

from app.research.netguard import is_public_url

logger = logging.getLogger(__name__)

MAX_PAGE_BYTES = 400_000
MAX_REDIRECTS = 3

# Text that bot-protection and error pages show instead of the article. A real
# article can mention a captcha, so these only count on a short page or title.
BLOCK_MARKERS = (
    "just a moment",
    "one moment, please",
    "please wait while your request",
    "checking if the site connection is secure",
    "checking your browser",
    "enable javascript and cookies",
    "ray id",
    "attention required",
    "access denied",
    "verify you are human",
    "are you a robot",
    "unusual traffic",
    "request blocked",
)
BLOCK_PAGE_MAX_CHARS = 800


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


def is_block_page(text: str, title: str = "") -> bool:
    """True for a bot-challenge or error page that is not the source itself."""

    heading = (title or "").strip().lower()
    if any(heading.startswith(marker) for marker in BLOCK_MARKERS):
        return True
    body = " ".join((text or "").split()).lower()
    return len(body) <= BLOCK_PAGE_MAX_CHARS and any(marker in body for marker in BLOCK_MARKERS)


def fetch_page_text(url: str, limit: int) -> str:
    try:
        page = _download(url)
    except httpx.HTTPError as exc:
        logger.warning("Could not retrieve a source page: %s", exc.__class__.__name__)
        return ""
    if page is None:
        return ""
    raw, content_type = page
    text = text_from_html(raw) if "html" in content_type else " ".join(raw.split())
    if is_block_page(text):
        logger.warning("A source page returned a bot-challenge page instead of its text")
        return ""
    return text[:limit]


def _download(url: str) -> tuple[str, str] | None:
    """Fetch one page, checking every redirect target before it is requested."""

    current = url
    for _hop in range(MAX_REDIRECTS + 1):
        if not is_public_url(current):
            logger.warning("Refused to fetch a non-public address")
            return None
        with httpx.stream(
            "GET",
            current,
            timeout=8,
            follow_redirects=False,
            headers={
                # Identifies the client honestly. The "compatible" form is the usual
                # convention and is accepted by more sites than a bare name.
                "User-Agent": "Mozilla/5.0 (compatible; ProofLens/0.5; research desk)",
                "Accept": "text/html,text/plain;q=0.9,*/*;q=0.5",
                "Accept-Language": "en",
            },
        ) as response:
            if response.is_redirect:
                location = response.headers.get("location", "")
                if not location:
                    return None
                current = str(response.url.join(location))
                continue
            if response.status_code != 200:
                return None
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text/plain" not in content_type:
                return None
            chunks = []
            total = 0
            for chunk in response.iter_bytes():
                chunks.append(chunk)
                total += len(chunk)
                if total >= MAX_PAGE_BYTES:
                    break
            raw = b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
            return raw, content_type
    return None
