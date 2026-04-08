import uuid
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.research_question import ResearchQuestion


QUESTION = "What evidence links consistent sleep to memory consolidation in adults?"


def test_creates_and_reads_a_saved_question(client):
    created = client.post("/api/research", json={"question": f"  {QUESTION}  "})

    assert created.status_code == 201
    body = created.json()
    assert body["question"] == QUESTION
    assert body["status"] == "submitted"
    assert "report" not in body
    assert "claims" not in body
    assert "sources" not in body

    fetched = client.get(f"/api/research/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_lists_newest_question_first(client):
    older = client.post("/api/research", json={"question": QUESTION}).json()
    newer = client.post(
        "/api/research",
        json={"question": "Which studies dispute that claim about sleep and memory?"},
    ).json()

    with SessionLocal() as session:
        row = session.get(ResearchQuestion, uuid.UUID(older["id"]))
        row.created_at = datetime.now(timezone.utc) - timedelta(days=1)
        session.commit()

    listing = client.get("/api/research")
    assert listing.status_code == 200
    ids = [item["id"] for item in listing.json()]
    assert ids == [newer["id"], older["id"]]


def test_limit_is_applied(client):
    client.post("/api/research", json={"question": QUESTION})
    client.post(
        "/api/research",
        json={"question": "Which studies dispute that claim about sleep and memory?"},
    )

    response = client.get("/api/research?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_empty_history_is_an_empty_list(client):
    response = client.get("/api/research")
    assert response.status_code == 200
    assert response.json() == []


def test_short_question_is_rejected(client):
    response = client.post("/api/research", json={"question": "   too short  "})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert "10 characters" in body["error"]["message"]


def test_missing_question_is_not_found(client):
    missing_id = uuid.uuid4()
    response = client.get(f"/api/research/{missing_id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_limit_must_be_in_range(client):
    response = client.get("/api/research?limit=0")
    assert response.status_code == 422


def test_malformed_id_is_rejected(client):
    response = client.get("/api/research/not-a-uuid")
    assert response.status_code == 422
