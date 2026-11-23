"""Token totals and an approximate model cost for one research run.

The prices are configuration, not an invoice. A provider bill can differ.
"""

from contextvars import ContextVar, Token
from dataclasses import dataclass

from app.core.config import get_settings
from app.research.errors import ResearchError


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0


_current: ContextVar[Usage | None] = ContextVar("research_usage", default=None)


def start_usage(prompt_tokens: int = 0, completion_tokens: int = 0) -> Token:
    return _current.set(Usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens))


def reset_usage(token: Token) -> None:
    _current.reset(token)


def usage_is_active() -> bool:
    return _current.get() is not None


def current_usage() -> Usage:
    usage = _current.get()
    if usage is None:
        return Usage()
    return usage


def record_usage(prompt_tokens: int, completion_tokens: int) -> None:
    usage = _current.get()
    if usage is None:
        return
    usage.prompt_tokens += max(int(prompt_tokens), 0)
    usage.completion_tokens += max(int(completion_tokens), 0)


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return round(_raw_cost(prompt_tokens, completion_tokens), 6)


def assert_within_budget() -> None:
    usage = current_usage()
    cost = _raw_cost(usage.prompt_tokens, usage.completion_tokens)
    limit = get_settings().max_run_cost_usd
    if cost > limit:
        raise ResearchError(
            "This run stopped because it reached the configured cost limit.",
            retryable=False,
        )


def _raw_cost(prompt_tokens: int, completion_tokens: int) -> float:
    settings = get_settings()
    prompt = (max(prompt_tokens, 0) / 1_000_000) * settings.prompt_price_per_million
    completion = (max(completion_tokens, 0) / 1_000_000) * settings.completion_price_per_million
    return prompt + completion
