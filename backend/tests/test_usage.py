import uuid
from types import SimpleNamespace

import pytest

from app.mcp import tools
from app.mcp.client import _count_tokens
from app.research import model as model_module
from app.research.contracts import Verdict
from app.research.errors import ResearchError
from app.research.persist import save_progress
from app.research.usage import current_usage, record_usage, reset_usage, start_usage

QUESTION = "What share of adults in the trial slept under six hours?"
VERDICT = Verdict(
    status="Verified",
    explanation="Stated.",
    supporting_excerpt="20 percent slept under six hours",
    opposing_excerpt="",
)


class FakeCompletions:
    def parse(self, **_kwargs):
        message = SimpleNamespace(parsed=VERDICT)
        usage = SimpleNamespace(prompt_tokens=1200, completion_tokens=300)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


class FakeOpenAI:
    def __init__(self, **_kwargs):
        self.chat = SimpleNamespace(completions=FakeCompletions())


def test_parse_model_records_token_use(monkeypatch, set_env):
    set_env(OPENAI_API_KEY="test-key-not-real")
    monkeypatch.setattr(model_module, "OpenAI", FakeOpenAI)
    token = start_usage()
    try:
        model_module.parse_model(Verdict, "system", "user")
        usage = current_usage()
    finally:
        reset_usage(token)

    assert (usage.prompt_tokens, usage.completion_tokens) == (1200, 300)


def test_verify_tool_returns_its_tokens_so_the_api_process_can_count_them(monkeypatch, set_env):
    set_env(OPENAI_API_KEY="test-key-not-real")
    monkeypatch.setattr(model_module, "OpenAI", FakeOpenAI)

    result = tools.verify_claim(
        "20 percent of adults slept under six hours.",
        "A trial reported that 20 percent slept under six hours on weeknights.",
    )

    assert result["prompt_tokens"] == 1200
    assert result["completion_tokens"] == 300


def test_client_adds_tool_tokens_to_the_run_and_enforces_the_cap(set_env):
    set_env(MAX_RUN_COST_USD="1.0")
    token = start_usage()
    try:
        payload = {"status": "Verified", "prompt_tokens": 400, "completion_tokens": 100}
        _count_tokens(payload)
        usage = current_usage()
    finally:
        reset_usage(token)

    assert (usage.prompt_tokens, usage.completion_tokens) == (400, 100)
    assert payload == {"status": "Verified"}

    set_env(MAX_RUN_COST_USD="0")
    token = start_usage()
    try:
        with pytest.raises(ResearchError):
            _count_tokens({"prompt_tokens": 1, "completion_tokens": 0})
    finally:
        reset_usage(token)


def test_saved_progress_stores_the_usage_and_the_api_returns_it(client):
    created = client.post("/api/research", json={"question": QUESTION}).json()
    token = start_usage()
    try:
        record_usage(2_000_000, 1_000_000)
        save_progress(uuid.UUID(created["id"]), {})
    finally:
        reset_usage(token)

    saved = client.get(f"/api/research/{created['id']}").json()

    assert saved["prompt_tokens"] == 2_000_000
    assert saved["completion_tokens"] == 1_000_000
    assert saved["estimated_cost_usd"] == pytest.approx(0.9)
