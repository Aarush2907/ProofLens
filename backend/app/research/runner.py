import logging
import uuid

from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from app.core.config import get_settings
from app.research.checkpointer import get_checkpointer
from app.research.graph import build_graph
from app.research.persist import save_progress
from app.research.state import initial_state

logger = logging.getLogger(__name__)


def execute_research(question_id: uuid.UUID) -> None:
    """Run one saved question until the human review checkpoint or the report."""

    from app.core.database import SessionLocal
    from app.models.research_question import ResearchQuestion

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

    graph = build_graph(checkpointer=get_checkpointer(), pause_for_review=True)
    run_until_pause(graph, question_id, question)


def resume_research(question_id: uuid.UUID, decision: dict) -> None:
    """Continue the saved thread after the reviewer approves, rejects, or asks for more."""

    from app.core.database import SessionLocal
    from app.models.research_question import ResearchQuestion

    db = SessionLocal()
    try:
        record = db.get(ResearchQuestion, question_id)
        if record is None:
            return
        question = record.question
        record.status = "running"
        record.error_message = None
        db.commit()
    finally:
        db.close()

    graph = build_graph(checkpointer=get_checkpointer(), pause_for_review=True)
    run_until_pause(graph, question_id, question, resume=decision)


def run_until_pause(graph, question_id: uuid.UUID, question: str, resume: dict | None = None) -> dict:
    config = {
        "recursion_limit": get_settings().graph_recursion_limit,
        "configurable": {"thread_id": str(question_id)},
    }
    if resume is not None and not _waiting(graph, config):
        _keep_saved_work(
            question_id,
            "This review cannot be resumed because its workflow checkpoint is not available. "
            "A PostgreSQL checkpoint survives an API restart. An in-memory checkpoint does not.",
        )
        return initial_state(question)
    incoming = Command(resume=resume) if resume is not None else initial_state(question)
    state = initial_state(question)
    paused = False
    try:
        for snapshot in graph.stream(incoming, config, stream_mode="values"):
            state = snapshot
            save_progress(question_id, state, finished=False)
    except GraphInterrupt:
        paused = True
    except Exception:
        logger.exception("Research run failed for %s", question_id)
        state = {**state, "failed": True, "last_error": "Research stopped because a step failed."}

    if not state.get("failed") and (paused or _waiting(graph, config)):
        state = {**state, "stage": "awaiting_review", "failed": False, "last_error": ""}
        save_progress(question_id, state, finished=False)
        return state

    save_progress(question_id, state, finished=True)
    _mark_failed(question_id, state)
    return state


def _waiting(graph, config) -> bool:
    try:
        snapshot = graph.get_state(config)
    except Exception:
        logger.exception("Could not read the research checkpoint")
        return False
    if getattr(snapshot, "interrupts", None):
        return True
    for task in getattr(snapshot, "tasks", None) or []:
        if getattr(task, "interrupts", None):
            return True
    return False


def _keep_saved_work(question_id: uuid.UUID, message: str) -> None:
    from app.core.database import SessionLocal
    from app.models.research_question import ResearchQuestion

    db = SessionLocal()
    try:
        record = db.get(ResearchQuestion, question_id)
        if record is None:
            return
        record.status = "running"
        record.stage = "awaiting_review"
        record.error_message = message
        db.commit()
    finally:
        db.close()


def _mark_failed(question_id: uuid.UUID, state: dict) -> None:
    if not state.get("failed"):
        return
    from app.core.database import SessionLocal
    from app.models.research_question import FAILED, ResearchQuestion

    db = SessionLocal()
    try:
        record = db.get(ResearchQuestion, question_id)
        if record is not None and record.status != FAILED:
            record.status = FAILED
            record.stage = "failed"
            record.error_message = state.get("last_error") or "Research stopped because a step failed."
            db.commit()
    finally:
        db.close()
