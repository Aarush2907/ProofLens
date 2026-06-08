import json
import uuid

from test_research_graph import scripted_model, search_hits

from app.api.research import _activity_stream
from app.research.activity import activity_log
from app.research.graph import build_graph
from app.research.state import initial_state


class DisconnectAfter:
    def __init__(self, after: int):
        self.calls = 0
        self.after = after

    async def is_disconnected(self) -> bool:
        self.calls += 1
        return self.calls > self.after


def test_graph_emits_events_from_the_agents():
    session_id = str(uuid.uuid4())
    build_graph(
        model=scripted_model,
        search=search_hits,
        fetch_page=lambda _url, _limit: "",
    ).invoke(initial_state("What evidence links sleep and memory?", session_id=session_id))

    events = activity_log.since(session_id, 0)
    kinds = [event["kind"] for event in events]
    for kind in (
        "researcher_started",
        "searching",
        "source_discovered",
        "sources_collected",
        "extractor_started",
        "claims_extracted",
        "fact_checker_started",
        "claim_verified",
        "contradiction_detector_started",
        "contradiction_detected",
        "writer_started",
        "report_completed",
    ):
        assert kind in kinds
    assert events[-1]["terminal"] is True
    assert any(event["detail"].get("url", "").startswith("https://") for event in events)


def test_stream_replays_saved_events_and_then_stops(client):
    created = client.post(
        "/api/research",
        json={"question": "What evidence links sleep and memory consolidation?"},
    ).json()
    session_id = created["id"]
    activity_log.record(session_id, "researcher_started", "Researcher agent started.", agent="researcher")
    activity_log.record(session_id, "searching", "Searching the web.", agent="researcher", detail={"query": "sleep"})
    finished = activity_log.record(
        session_id,
        "research_failed",
        "Search API key is not configured.",
        agent="workflow",
        terminal=True,
    )

    with client.stream("GET", f"/api/research/{session_id}/events") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    assert "Researcher agent started." in body
    assert "Searching the web." in body
    assert "Search API key is not configured." in body

    resumed = client.stream(
        "GET",
        f"/api/research/{session_id}/events",
        headers={"Last-Event-ID": str(finished["id"] - 1)},
    )
    with resumed as response:
        body = "".join(response.iter_text())
    payloads = [json.loads(line[6:]) for line in body.splitlines() if line.startswith("data: ")]
    assert [item["id"] for item in payloads] == [finished["id"]]
    assert client.get("/api/health").status_code == 200


def test_stream_stops_when_the_client_disconnects():
    session_id = str(uuid.uuid4())
    activity_log.record(session_id, "research_started", "Research started.", agent="workflow")

    async def read():
        chunks = []
        async for chunk in _activity_stream(session_id, 0, DisconnectAfter(1)):
            chunks.append(chunk)
        return chunks

    import asyncio

    chunks = asyncio.run(read())
    assert any("Research started." in chunk for chunk in chunks)


def test_missing_session_does_not_open_a_stream(client):
    response = client.get(f"/api/research/{uuid.uuid4()}/events")
    assert response.status_code == 404
