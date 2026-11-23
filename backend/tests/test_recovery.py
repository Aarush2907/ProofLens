import uuid

from app.core.database import SessionLocal
from app.models.research_question import ResearchQuestion
from app.research.recovery import INTERRUPTED_MESSAGE, mark_interrupted_runs

QUESTION = "What share of adults in the trial slept under six hours?"


def _saved(question_id: str) -> tuple[str, str, str | None]:
    db = SessionLocal()
    try:
        row = db.get(ResearchQuestion, uuid.UUID(question_id))
        return row.status, row.stage, row.error_message
    finally:
        db.close()


def test_a_restart_fails_an_unfinished_run_but_keeps_one_awaiting_review(client):
    working = client.post("/api/research", json={"question": QUESTION}).json()
    waiting = client.post("/api/research", json={"question": QUESTION}).json()
    db = SessionLocal()
    try:
        db.get(ResearchQuestion, uuid.UUID(waiting["id"])).stage = "awaiting_review"
        db.commit()
    finally:
        db.close()

    assert mark_interrupted_runs() == 1

    assert _saved(working["id"]) == ("failed", "failed", INTERRUPTED_MESSAGE)
    assert _saved(waiting["id"]) == ("running", "awaiting_review", None)
