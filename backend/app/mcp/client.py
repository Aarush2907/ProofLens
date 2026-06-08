"""Synchronous client for the ProofLens MCP server.

The LangGraph nodes are ordinary functions. This client keeps one stdio
session on a background thread and gives those nodes a blocking call with a
timeout. Tool execution stays in the server process.
"""

import asyncio
import json
import os
import sys
import threading
from concurrent.futures import TimeoutError as FutureTimeout
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.core.config import get_settings
from app.research.contracts import SearchHit
from app.research.errors import ResearchError

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_executor = None
_executor_lock = threading.Lock()


class McpToolExecutor:
    def __init__(self):
        self._loop = None
        self._thread = None
        self._session = None
        self._ready = threading.Event()
        self._failed = None
        self._call_lock = threading.Lock()
        self._start_lock = threading.Lock()

    def start(self) -> None:
        with self._start_lock:
            if self._thread is None:
                self._thread = threading.Thread(target=self._run_loop, name="prooflens-mcp", daemon=True)
                self._thread.start()
        timeout = get_settings().mcp_tool_timeout_seconds
        if not self._ready.wait(timeout):
            raise ResearchError("The MCP research server did not start.", retryable=True)
        if self._failed is not None:
            raise ResearchError("The MCP research server did not start.", retryable=True) from self._failed

    def search(self, query: str, limit: int) -> list[SearchHit]:
        payload = self._call("search_web", {"query": query, "limit": limit})
        hits = []
        for item in payload.get("results") or []:
            hits.append(
                SearchHit(
                    title=item.get("title") or item.get("url") or "",
                    url=item.get("url") or "",
                    snippet=item.get("snippet") or "",
                    content=item.get("snippet") or "",
                    query=item.get("query") or query,
                    published_on=item.get("published_on") or "",
                    author=item.get("author") or "",
                )
            )
        return hits

    def fetch(self, url: str, limit: int, source_id: str = "", title: str = "", session_id: str = "") -> dict:
        return self._call(
            "retrieve_source",
            {
                "url": url,
                "limit": limit,
                "session_id": session_id,
                "source_id": source_id,
                "title": title,
            },
        )

    def extract(self, sources: list[dict]) -> list[dict]:
        packet = [
            {
                "url": source.get("url") or "",
                "title": source.get("title") or "",
                "text": source.get("content") or source.get("snippet") or "",
            }
            for source in sources
        ]
        payload = self._call("extract_claims", {"sources": packet})
        return list(payload.get("claims") or [])

    def verify(self, claim: str, passage: str) -> dict:
        return self._call("verify_claim", {"claim": claim, "passage": passage})

    def evidence(self, query: str, session_id: str) -> list[dict]:
        payload = self._call(
            "search_evidence",
            {"query": query, "session_id": session_id, "limit": 4},
        )
        return list(payload.get("passages") or [])

    def _call(self, name: str, arguments: dict) -> dict:
        self.start()
        timeout = get_settings().mcp_tool_timeout_seconds
        with self._call_lock:
            future = asyncio.run_coroutine_threadsafe(
                self._session.call_tool(name, arguments, read_timeout_seconds=timeout),
                self._loop,
            )
            try:
                result = future.result(timeout=timeout)
            except FutureTimeout as exc:
                future.cancel()
                raise ResearchError(f"The {name} tool timed out.", retryable=True) from exc
            except ResearchError:
                raise
            except Exception as exc:
                raise ResearchError(f"The {name} tool failed.", retryable=True) from exc
        return _payload(name, result)

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception as exc:
            self._failed = exc
            self._ready.set()

    async def _serve(self) -> None:
        environment = {key: value for key, value in os.environ.items() if isinstance(value, str)}
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "app.mcp.server"],
            cwd=str(_BACKEND_ROOT),
            env=environment,
        )
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                self._ready.set()
                await asyncio.Event().wait()


def get_executor() -> McpToolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = McpToolExecutor()
        return _executor


def _payload(name: str, result) -> dict:
    if getattr(result, "is_error", False):
        message = _text(result) or f"The {name} tool failed."
        prefix = f"Error executing tool {name}: "
        if message.startswith(prefix):
            message = message[len(prefix) :]
        raise ResearchError(message, retryable=False)
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    raw = _text(result)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResearchError(f"The {name} tool returned an unreadable result.", retryable=True) from exc
    if not isinstance(parsed, dict):
        raise ResearchError(f"The {name} tool returned an unreadable result.", retryable=True)
    return parsed


def _text(result) -> str:
    parts = []
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", "")
        if text:
            parts.append(text)
    return "\n".join(parts).strip()
