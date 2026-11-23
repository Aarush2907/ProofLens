import pytest

from app.research.errors import ResearchError
from app.research.limits import RunLimiter
from app.research.usage import assert_within_budget, record_usage, reset_usage, start_usage


QUESTION = "What share of adults in the trial slept under six hours?"


def test_limiter_stops_an_extra_concurrent_run_and_an_extra_start():
    limiter = RunLimiter(max_concurrent=1, max_starts=2, window_seconds=60)

    assert limiter.try_acquire() is True
    assert limiter.try_acquire() is False
    limiter.release()
    assert limiter.try_acquire() is True
    limiter.release()
    assert limiter.try_acquire() is False


def test_research_post_returns_429_when_the_start_cap_is_reached(client, monkeypatch):
    limiter = RunLimiter(max_concurrent=3, max_starts=1, window_seconds=600)
    monkeypatch.setattr("app.api.research.get_run_limiter", lambda: limiter)

    first = client.post("/api/research", json={"question": QUESTION})
    second = client.post("/api/research", json={"question": QUESTION})

    assert first.status_code == 201
    assert second.status_code == 429
    assert second.json()["error"]["code"] == "rate_limited"


def test_a_run_slot_is_released_when_the_background_run_ends(client, monkeypatch):
    limiter = RunLimiter(max_concurrent=1, max_starts=10, window_seconds=600)
    monkeypatch.setattr("app.api.research.get_run_limiter", lambda: limiter)

    assert client.post("/api/research", json={"question": QUESTION}).status_code == 201
    assert client.post("/api/research", json={"question": QUESTION}).status_code == 201


def test_cost_limit_is_not_retried(set_env):
    set_env(MAX_RUN_COST_USD="0")
    token = start_usage()
    try:
        record_usage(1, 0)
        with pytest.raises(ResearchError) as raised:
            assert_within_budget()
    finally:
        reset_usage(token)

    assert raised.value.retryable is False
