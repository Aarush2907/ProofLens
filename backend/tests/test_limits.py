from app.core.config import get_settings
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


def test_cost_limit_is_not_retried(monkeypatch):
    monkeypatch.setenv("MAX_RUN_COST_USD", "0")
    get_settings.cache_clear()
    token = start_usage()
    try:
        record_usage(1, 0)
        try:
            assert_within_budget()
            raised = False
        except ResearchError as exc:
            raised = True
            assert exc.retryable is False
        assert raised is True
    finally:
        reset_usage(token)
        get_settings.cache_clear()
