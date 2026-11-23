import httpx

from app.research import pages
from app.research.netguard import is_public_url


def test_loopback_and_private_addresses_are_not_public():
    assert is_public_url("http://127.0.0.1/admin") is False
    assert is_public_url("http://10.0.0.5/") is False
    assert is_public_url("http://169.254.169.254/latest/meta-data") is False
    assert is_public_url("http://[::1]:6333/") is False
    assert is_public_url("file:///etc/passwd") is False


def test_a_page_on_a_private_address_is_never_requested(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("A request was sent to a private address.")

    monkeypatch.setattr(httpx, "stream", fail)

    assert pages.fetch_page_text("http://127.0.0.1:6333/collections", 1000) == ""


def test_a_redirect_to_a_private_address_is_refused(monkeypatch):
    requested = []

    def public_only(url: str) -> bool:
        return "internal" not in url

    class Redirect:
        is_redirect = True
        headers = {"location": "http://internal.local/secret"}
        url = httpx.URL("https://example.edu/start")

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def stream(_method, url, **_kwargs):
        requested.append(url)
        return Redirect()

    monkeypatch.setattr(pages, "is_public_url", public_only)
    monkeypatch.setattr(httpx, "stream", stream)

    assert pages.fetch_page_text("https://example.edu/start", 1000) == ""
    assert requested == ["https://example.edu/start"]
