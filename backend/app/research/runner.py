import logging
import uuid

from app.core.config import get_settings
from app.research.graph import build_graph
from app.research.persist import save_progress
from app.research.state import initial_state

logger = logging.getLogger(__name__)


def execute_research(question_id: uuid.UUID) -> None:
    """Run one saved question through the graph and store each finished step."""

    from app.models.research_question import FAILED, ResearchQuestion
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        record = db.get(ResearchQuestion, question_id)
        if record is None:
            return
        question = record.question
        record.status = "running"
        record.stage = "researching"
        record.error_message = None
        db.commit()
    finally:
        db.close()

    state = initial_state(question)
    try:
        graph = build_graph()
        config = {"recursion_limit": get_settings().graph_recursion_limit}
        for snapshot in graph.stream(state, config, stream_mode="values"):
            state = snapshot
            save_progress(question_id, state, finished=False)
    except Exception:
        logger.exception("Research run failed for %s", question_id)
        state = {**state, "failed": True, "last_error": "Research stopped because a step failed."}

    save_progress(question_id, state, finished=True)
    if state.get("failed"):
        db = SessionLocal()
        try:
            record = db.get(ResearchQuestion, question_id)
            if record is not None and record.status != FAILED:
                record.status = FAILED
                record.stage = "failed"
                db.commit()
        finally:
            db.close()
