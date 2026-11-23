"""API keys supplied by the person running a question.

A hosted ProofLens should not spend the host's keys. The browser sends the
visitor's own keys with a request, and they live only in this context while
the run works. They are never written to the database, the activity log, or
the application log.
"""

from contextvars import ContextVar, Token
from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class Credentials:
    openai_api_key: str = ""
    search_api_key: str = ""


_current: ContextVar[Credentials | None] = ContextVar("research_credentials", default=None)


def use_credentials(credentials: Credentials) -> Token:
    return _current.set(credentials)


def reset_credentials(token: Token) -> None:
    _current.reset(token)


def supplied() -> Credentials:
    """The keys the visitor sent, with no fallback to the server's own."""

    return _current.get() or Credentials()


def openai_key() -> str:
    return supplied().openai_api_key or _server_key(get_settings().openai_api_key)


def search_key() -> str:
    return supplied().search_api_key or _server_key(get_settings().search_api_key)


def missing_keys(credentials: Credentials) -> list[str]:
    """Names of the keys a run could not use, given what was sent."""

    settings = get_settings()
    missing = []
    if not (credentials.openai_api_key or _server_key(settings.openai_api_key)):
        missing.append("OpenAI")
    if not (credentials.search_api_key or _server_key(settings.search_api_key)):
        missing.append("Tavily search")
    return missing


def _server_key(value: str) -> str:
    # With REQUIRE_USER_KEYS the host's own keys are never used for a visitor.
    return "" if get_settings().require_user_keys else value
