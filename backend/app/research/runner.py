import logging
import time
import uuid

from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from app.core.config import get_settings
from app.research.activity import bind_session, emit, reset_session
from app.research.checkpointer import get_checkpointer
from app.research.graph import build_graph
from app.research.persist import save_progress
from app.research.state import initial_state
from app.research.usage import current_usage, estimate_cost, reset_usage, start_usage

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
        prompt_tokens = record.prompt_tokens or 0
        completion_tokens = record.completion_tokens or 0
        record.status = "running"
        record.stage = "researching"
        record.error_message = None
        db.commit()
    finally:
        db.close()

    _run_tracked(question_id, question, prompt_tokens, completion_tokens, resume=None)


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
        prompt_tokens = record.prompt_tokens or 0
        completion_tokens = record.completion_tokens or 0
        record.status = "running"
        record.error_message = None
        db.commit()
    finally:
        db.close()

    _run_tracked(question_id, question, prompt_tokens, completion_tokens, resume=decision)


def _run_tracked(
    question_id: uuid.UUID,
    question: str,
    prompt_tokens: int,
    completion_tokens: int,
    resume: dict | None,
) -> None:
    graph = build_graph(checkpointer=get_checkpointer(), pause_for_review=True)
    session_token = bind_session(str(question_id))
    usage_token = start_usage(prompt_tokens, completion_tokens)
    started = time.perf_counter()
    logger.info("Research session %s started", question_id)
    try:
        if resume is None:
            emit("research_started", "Research started.", agent="workflow", session_id=str(question_id))
        run_until_pause(graph, question_id, question, resume=resume)
    finally:
        usage = current_usage()
        logger.info(
            "Research session %s stopped duration_seconds=%.2f prompt_tokens=%s completion_tokens=%s estimated_cost_usd=%.6f",
            question_id,
            time.perf_counter() - started,
            usage.prompt_tokens,
            usage.completion_tokens,
            estimate_cost(usage.prompt_tokens, usage.completion_tokens),
        )
        reset_session(session_token)
        reset_usage(usage_token)


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
    incoming = Command(resume=resume) if resume is not None else initial_state(question, session_id=str(question_id))
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
    if state.get("failed"):
        emit(
            "research_failed",
            state.get("last_error") or "Research stopped because a step failed.",
            agent="workflow",
            terminal=True,
            session_id=str(question_id),
        )
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
