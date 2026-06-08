import asyncio
import uuid

import pytest

from mcp.client._memory import InMemoryTransport
from mcp.client.session import ClientSession

from app.mcp import tools
from app.mcp.client import McpToolExecutor, _payload
from app.mcp.server import server
from app.research.agents.fact_checker import check_claims
from app.research.contracts import ClaimBatch, ExtractedClaim, SearchHit, Verdict
from app.research.errors import ResearchError
from app.research.index import get_index

PASSAGE = (
    "Adults who slept seven hours recalled 20 percent more word pairs than adults who slept four hours."
)


async def _call(name: str, arguments: dict):
    async with InMemoryTransport(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            return listed, await session.call_tool(name, arguments)


def test_mcp_server_lists_the_research_tools():
    async def list_only():
        async with InMemoryTransport(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                return listed

    listed = asyncio.run(list_only())
    names = {tool.name for tool in listed.tools}
    assert names == {"search_web", "retrieve_source", "extract_claims", "verify_claim", "search_evidence"}
    search = next(tool for tool in listed.tools if tool.name == "search_web")
    assert "query" in search.input_schema["properties"]
    assert search.output_schema["properties"]["results"]["type"] == "array"


def test_mcp_search_returns_structured_results(monkeypatch):
    monkeypatch.setattr(
        tools,
        "search_provider",
        lambda query, limit: [
            SearchHit(title="Study A", url="https://example.edu/sleep-a", snippet=PASSAGE, query=query)
        ],
    )
    _listed, result = asyncio.run(_call("search_web", {"query": "sleep and memory", "limit": 2}))
    assert result.is_error is False
    assert result.structured_content["results"][0]["url"] == "https://example.edu/sleep-a"


def test_mcp_rejects_an_empty_query_and_a_bad_url():
    empty = asyncio.run(_call("search_web", {"query": "   ", "limit": 2}))[1]
    assert empty.is_error is True
    assert "query is required" in empty.content[0].text

    missing = asyncio.run(_call("search_web", {"limit": 2}))[1]
    assert missing.is_error is True

    bad_url = asyncio.run(_call("retrieve_source", {"url": "not-a-url"}))[1]
    assert bad_url.is_error is True
    assert "http" in bad_url.content[0].text


def test_mcp_workflow_stores_a_page_and_the_fact_checker_uses_it(monkeypatch):
    get_index.cache_clear()
    monkeypatch.setattr(tools, "fetch_page_text", lambda url, limit: PASSAGE)

    def model(schema, _system, user):
        if schema is ClaimBatch:
            return ClaimBatch(
                claims=[ExtractedClaim(source_url="https://example.edu/sleep-a", text=PASSAGE, kind="statistic")]
            )
        if schema is Verdict:
            if "20 percent" not in user:
                return Verdict(status="Insufficient evidence", explanation="The figure is not in the passage.")
            return Verdict(
                status="Verified",
                explanation="The passage states this figure.",
                supporting_excerpt=PASSAGE,
            )
        raise AssertionError(schema.__name__)

    monkeypatch.setattr(tools, "parse_model", model)
    session_id = str(uuid.uuid4())
    source_id = str(uuid.uuid4())
    retrieved = asyncio.run(
        _call(
            "retrieve_source",
            {
                "url": "https://example.edu/sleep-a",
                "limit": 4000,
                "session_id": session_id,
                "source_id": source_id,
                "title": "Study A",
            },
        )
    )[1]
    assert retrieved.is_error is False
    assert "20 percent" in retrieved.structured_content["text"]

    extracted = asyncio.run(
        _call(
            "extract_claims",
            {"sources": [{"url": "https://example.edu/sleep-a", "title": "Study A", "text": PASSAGE}]},
        )
    )[1]
    assert extracted.is_error is False
    assert extracted.structured_content["claims"][0]["text"] == PASSAGE

    found = asyncio.run(
        _call("search_evidence", {"query": "sleep memory word pairs", "session_id": session_id, "limit": 3})
    )[1]
    assert found.is_error is False
    passages = found.structured_content["passages"]
    assert passages
    assert passages[0]["source_id"] == source_id
    assert passages[0]["url"] == "https://example.edu/sleep-a"

    checked = asyncio.run(_call("verify_claim", {"claim": PASSAGE, "passage": passages[0]["text"]}))[1]
    assert checked.structured_content["status"] == "Verified"

    state = {
        "session_id": session_id,
        "sources": [
            {
                "id": source_id,
                "url": "https://example.edu/sleep-a",
                "title": "Study A",
                "snippet": "Study A",
                "content": "Study A",
            }
        ],
        "claims": [
            {
                "id": str(uuid.uuid4()),
                "source_id": source_id,
                "source_url": "https://example.edu/sleep-a",
                "text": PASSAGE,
                "kind": "statistic",
            }
        ],
    }
    result = check_claims(
        state,
        model,
        retrieve_evidence=lambda query, session: tools.search_evidence(query, session)["passages"],
        verify=lambda claim, passage: tools.verify_claim(claim, passage),
    )
    verdict = result["verifications"][0]
    assert verdict["status"] == "Verified"
    assert verdict["supporting_excerpt"] == PASSAGE

    without_retrieval = check_claims(state, model)
    assert without_retrieval["verifications"][0]["status"] == "Insufficient evidence"
    get_index.cache_clear()


def test_stdio_server_starts_and_answers_search_evidence():
    executor = McpToolExecutor()
    try:
        payload = executor._call(
            "search_evidence",
            {"query": "sleep and memory", "session_id": str(uuid.uuid4()), "limit": 2},
        )
        assert payload["passages"] == []
        with pytest.raises(ResearchError, match="query is required"):
            executor._call("search_web", {"query": " ", "limit": 1})
    finally:
        executor._loop.call_soon_threadsafe(executor._loop.stop) if executor._loop else None


def test_tool_timeout_is_reported(monkeypatch):
    import asyncio as asyncio_module
    import threading

    class SlowSession:
        async def call_tool(self, name, arguments, read_timeout_seconds=None):
            await asyncio_module.sleep(2)
            return None

    class Settings:
        mcp_tool_timeout_seconds = 0.05

    loop = asyncio_module.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()
    executor = McpToolExecutor()
    executor._thread = thread
    executor._loop = loop
    executor._session = SlowSession()
    executor._ready.set()
    monkeypatch.setattr("app.mcp.client.get_settings", lambda: Settings())
    try:
        with pytest.raises(ResearchError, match="timed out"):
            executor._call("search_web", {"query": "sleep", "limit": 1})
    finally:
        loop.call_soon_threadsafe(loop.stop)


def test_error_payload_is_not_treated_as_a_result():
    class Block:
        text = "Error executing tool search_web: query is required"

    class Result:
        is_error = True
        structured_content = None
        content = [Block()]

    with pytest.raises(ResearchError, match="query is required"):
        _payload("search_web", Result())
