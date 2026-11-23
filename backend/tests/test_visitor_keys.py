from app.mcp.client import _key_arguments
from app.research.visitor_keys import Credentials, openai_key, search_key, use_credentials, reset_credentials

QUESTION = "What share of adults in the trial slept under six hours?"


def test_visitor_keys_reach_the_run_and_are_not_stored(client):
    seen = {}

    def run(_question_id):
        seen["openai"] = openai_key()
        seen["search"] = search_key()

    from app.main import app
    from app.services.research import get_research_runner

    app.dependency_overrides[get_research_runner] = lambda: run
    created = client.post(
        "/api/research",
        json={"question": QUESTION},
        headers={"X-OpenAI-Key": "visitor-openai", "X-Search-Key": "visitor-search"},
    )

    assert created.status_code == 201
    assert seen == {"openai": "visitor-openai", "search": "visitor-search"}
    assert "visitor-openai" not in created.text
    assert "visitor-openai" not in client.get(f"/api/research/{created.json()['id']}").text
    assert openai_key() == ""


def test_a_key_required_host_refuses_a_run_without_keys_and_saves_nothing(client, set_env):
    set_env(REQUIRE_USER_KEYS="true", OPENAI_API_KEY="host-key", SEARCH_API_KEY="host-search")

    refused = client.post("/api/research", json={"question": QUESTION})

    assert refused.status_code == 400
    assert refused.json()["error"]["code"] == "keys_required"
    assert "OpenAI" in refused.json()["error"]["message"]
    assert client.get("/api/research").json() == []

    allowed = client.post(
        "/api/research",
        json={"question": QUESTION},
        headers={"X-OpenAI-Key": "a", "X-Search-Key": "b"},
    )
    assert allowed.status_code == 201


def test_the_host_keys_are_never_used_when_user_keys_are_required(set_env):
    set_env(REQUIRE_USER_KEYS="true", OPENAI_API_KEY="host-key", SEARCH_API_KEY="host-search")

    assert openai_key() == ""
    assert search_key() == ""
    token = use_credentials(Credentials(openai_api_key="mine"))
    try:
        assert openai_key() == "mine"
    finally:
        reset_credentials(token)


def test_the_host_keys_are_used_when_user_keys_are_not_required(set_env):
    set_env(REQUIRE_USER_KEYS="false", OPENAI_API_KEY="host-key")

    assert openai_key() == "host-key"


def test_only_the_tool_that_needs_a_key_receives_it():
    token = use_credentials(Credentials(openai_api_key='mine', search_api_key='theirs'))
    try:
        assert _key_arguments('search_web') == {'search_api_key': 'theirs'}
        assert _key_arguments('verify_claim') == {'openai_api_key': 'mine'}
        assert _key_arguments('retrieve_source') == {}
    finally:
        reset_credentials(token)
    assert _key_arguments('verify_claim') == {}
