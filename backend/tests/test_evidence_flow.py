import uuid

from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from test_research_graph import PASSAGE_A, PASSAGE_B, URL_A, URL_B, scripted_model, search_hits

from app.research.graph import build_graph
from app.research.runner import run_until_pause


def _graph(saver):
    return build_graph(
        model=scripted_model,
        search=search_hits,
        fetch_page=lambda _url, _limit: "",
        checkpointer=saver,
        pause_for_review=True,
    )


def test_review_pauses_before_the_report_and_resumes_one_session(client):
    created = client.post(
        "/api/research",
        json={"question": "What evidence links sleep and memory consolidation?"},
    ).json()
    other = client.post(
        "/api/research",
        json={"question": "Which studies dispute that claim about sleep and memory?"},
    ).json()
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    saver = SqliteSaver(connection)
    saver.setup()
    graph = _graph(saver)

    paused = run_until_pause(graph, uuid.UUID(created["id"]), created["question"])
    assert paused["stage"] == "awaiting_review"
    assert paused["report"] is None
    assert len(paused["sources"]) == 2
    assert {source["url"] for source in paused["sources"]} == {URL_A, URL_B}
    assert all(source["domain"] == "example.edu" for source in paused["sources"])
    assert all(source["url"] == URL_A or source["url"] == URL_B for source in paused["sources"])

    detail = client.get(f"/api/research/{created['id']}").json()
    assert detail["stage"] == "awaiting_review"
    assert detail["sources"][0]["quality"]["role"] == "unclear"
    assert "score" not in detail["sources"][0]["quality"]
    supporting = [
        item
        for claim in detail["claims"]
        for item in claim["evidence"]
        if item["stance"] == "supporting"
    ]
    opposing = [
        item
        for claim in detail["claims"]
        for item in claim["evidence"]
        if item["stance"] == "opposing"
    ]
    assert supporting
    assert opposing == []
    assert all(item["source_url"] in {URL_A, URL_B} for item in supporting)
    assert PASSAGE_A in {item["passage"] for item in supporting}
    assert PASSAGE_B in {item["passage"] for item in supporting}

    graph_body = client.get(f"/api/research/{created['id']}/graph").json()
    relations = {edge["relation"] for edge in graph_body["edges"]}
    assert "retrieved" in relations
    assert "extracted" in relations
    assert "supports" in relations
    assert "contradicts" not in relations
    assert "disagrees" in relations
    node_urls = {node["url"] for node in graph_body["nodes"] if node["url"]}
    assert node_urls <= {URL_A, URL_B}
    assert not any(node["url"].startswith("https://invented.example") for node in graph_body["nodes"])

    other_paused = run_until_pause(graph, uuid.UUID(other["id"]), other["question"])
    assert other_paused["stage"] == "awaiting_review"

    decisions = []
    for claim in detail["claims"]:
        decisions.append(
            {
                "claim_id": claim["id"],
                "decision": "rejected" if claim["kind"] == "opinion" else "approved",
            }
        )
    finished = run_until_pause(
        graph,
        uuid.UUID(created["id"]),
        created["question"],
        resume={"action": "continue", "decisions": decisions, "note": ""},
    )
    assert finished["stage"] == "report_written"
    assert finished["report"]["findings"][0]["citation_urls"] == [URL_A]
    assert any("rejected in review" in item for item in finished["report"]["limitations"])

    saved = client.get(f"/api/research/{created['id']}").json()
    assert saved["status"] == "completed"
    opinions = [claim for claim in saved["claims"] if claim["kind"] == "opinion"]
    assert opinions[0]["review_status"] == "rejected"
    assert opinions[0]["evidence"] == []
    assert all(url in {URL_A, URL_B} for finding in saved["report"]["findings"] for url in finding["citation_urls"])

    still_waiting = client.get(f"/api/research/{other['id']}").json()
    assert still_waiting["stage"] == "awaiting_review"
    assert still_waiting["report"] is None


def test_more_research_restarts_from_the_researcher_without_a_report(client):
    created = client.post(
        "/api/research",
        json={"question": "What evidence links sleep and memory consolidation?"},
    ).json()
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    saver = SqliteSaver(connection)
    saver.setup()
    graph = _graph(saver)
    question_id = uuid.UUID(created["id"])
    run_until_pause(graph, question_id, created["question"])
    again = run_until_pause(
        graph,
        question_id,
        created["question"],
        resume={"action": "research_more", "decisions": [], "note": "Look for a conflicting figure."},
    )
    assert again["stage"] == "awaiting_review"
    assert again["report"] is None
    assert again["review_rounds"] == 1
    assert again["trace"].count("researcher") == 2
    detail = client.get(f"/api/research/{created['id']}").json()
    assert detail["report"] is None
    assert detail["sources"]


def test_missing_excerpt_does_not_invent_an_evidence_edge(client):
    created = client.post(
        "/api/research",
        json={"question": "What evidence links sleep and memory consolidation?"},
    ).json()
    from app.research.persist import save_progress

    source_id = str(uuid.uuid4())
    claim_id = str(uuid.uuid4())
    save_progress(
        uuid.UUID(created["id"]),
        {
            "sources": [
                {
                    "id": source_id,
                    "url": URL_A,
                    "title": "Study A",
                    "domain": "example.edu",
                    "snippet": "Short.",
                    "content": "",
                    "search_query": "sleep",
                }
            ],
            "claims": [
                {
                    "id": claim_id,
                    "source_id": source_id,
                    "source_url": URL_A,
                    "text": "A claim with no quotable passage.",
                    "kind": "fact",
                    "review_status": "pending",
                }
            ],
            "verifications": [
                {
                    "claim_id": claim_id,
                    "status": "Insufficient evidence",
                    "explanation": "The source did not include a passage long enough to check this claim.",
                    "supporting_excerpt": "",
                    "opposing_excerpt": "",
                }
            ],
            "contradictions": [],
            "report": None,
            "failed": False,
            "stage": "awaiting_review",
        },
        finished=False,
    )
    graph_body = client.get(f"/api/research/{created['id']}/graph").json()
    assert [node["kind"] for node in graph_body["nodes"]].count("evidence") == 0
    assert "supports" not in {edge["relation"] for edge in graph_body["edges"]}
    assert "contradicts" not in {edge["relation"] for edge in graph_body["edges"]}
    claim = client.get(f"/api/research/{created['id']}").json()["claims"][0]
    assert claim["verification"]["status"] == "Insufficient evidence"
    assert claim["evidence"] == []


def test_opposing_excerpt_becomes_a_contradicting_edge(client):
    created = client.post(
        "/api/research",
        json={"question": "What evidence links sleep and memory consolidation?"},
    ).json()
    from app.research.persist import save_progress

    source_id = str(uuid.uuid4())
    claim_id = str(uuid.uuid4())
    save_progress(
        uuid.UUID(created["id"]),
        {
            "sources": [
                {
                    "id": source_id,
                    "url": URL_B,
                    "title": "Study B",
                    "domain": "example.edu",
                    "snippet": PASSAGE_B,
                    "content": PASSAGE_B,
                    "search_query": "sleep",
                }
            ],
            "claims": [
                {
                    "id": claim_id,
                    "source_id": source_id,
                    "source_url": URL_B,
                    "text": "Recall rose by 20 percent.",
                    "kind": "statistic",
                    "review_status": "pending",
                }
            ],
            "verifications": [
                {
                    "claim_id": claim_id,
                    "status": "Contradicted",
                    "explanation": "The passage states 5 percent, not 20 percent.",
                    "supporting_excerpt": "",
                    "opposing_excerpt": PASSAGE_B,
                }
            ],
            "stage": "awaiting_review",
            "failed": False,
        },
        finished=False,
    )
    body = client.get(f"/api/research/{created['id']}/graph").json()
    contradicts = [edge for edge in body["edges"] if edge["relation"] == "contradicts"]
    assert len(contradicts) == 1
    evidence = next(node for node in body["nodes"] if node["kind"] == "evidence")
    assert evidence["passage"] == PASSAGE_B
    assert evidence["url"] == URL_B


def test_review_endpoint_rejects_a_run_that_is_still_researching(client):
    created = client.post(
        "/api/research",
        json={"question": "What evidence links sleep and memory consolidation?"},
    ).json()
    response = client.post(
        f"/api/research/{created['id']}/review",
        json={"action": "continue", "decisions": []},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "not_awaiting_review"


def test_review_endpoint_requires_a_decision_for_every_claim(client):
    created = client.post(
        "/api/research",
        json={"question": "What evidence links sleep and memory consolidation?"},
    ).json()
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    saver = SqliteSaver(connection)
    saver.setup()
    run_until_pause(_graph(saver), uuid.UUID(created["id"]), created["question"])
    response = client.post(
        f"/api/research/{created['id']}/review",
        json={"action": "continue", "decisions": []},
    )
    assert response.status_code == 422
    assert "every" in response.json()["error"]["message"]
