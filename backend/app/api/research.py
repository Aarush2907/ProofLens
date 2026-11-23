import asyncio
import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, Request
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal, get_db
from app.core.errors import AppError
from app.research.activity import activity_log
from app.research.visitor_keys import (
    Credentials,
    missing_keys,
    reset_credentials,
    use_credentials,
)
from app.research.export import render_markdown, render_pdf
from app.research.limits import get_run_limiter
from app.models.research_question import ResearchQuestion
from app.schemas.research import (
    EvidenceGraphRead,
    ResearchQuestionCreate,
    ResearchQuestionRead,
    ResearchSessionRead,
    ReviewRequest,
)
from app.services.evidence_graph import load_evidence_graph
from app.services.research import (
    claim_ids_for,
    create_research_question,
    get_research_question,
    get_research_runner,
    get_review_runner,
    list_research_questions,
    load_research_session,
)

router = APIRouter(prefix="/research")

MAX_KEY_LENGTH = 300


def request_credentials(
    x_openai_key: str | None = Header(default=None),
    x_search_key: str | None = Header(default=None),
) -> Credentials:
    """Read the visitor's own keys. They are used for this request's run only."""

    openai_key = (x_openai_key or "").strip()
    search_key = (x_search_key or "").strip()
    if len(openai_key) > MAX_KEY_LENGTH or len(search_key) > MAX_KEY_LENGTH:
        raise AppError("An API key is too long.", status_code=422, code="validation_error")
    return Credentials(openai_api_key=openai_key, search_api_key=search_key)


def require_keys(credentials: Credentials) -> None:
    """Refuse a run on a key-required host before any row is saved."""

    if not get_settings().require_user_keys:
        return
    missing = missing_keys(credentials)
    if missing:
        names = " and ".join(missing)
        raise AppError(
            f"Add your {names} API key in Settings before starting a run.",
            status_code=400,
            code="keys_required",
        )


@router.get("", response_model=list[ResearchQuestionRead])
def read_research_questions(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ResearchQuestion]:
    return list_research_questions(db, limit)


@router.post("", response_model=ResearchQuestionRead, status_code=201)
def create_question(
    payload: ResearchQuestionCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    run_research=Depends(get_research_runner),
    credentials: Credentials = Depends(request_credentials),
) -> ResearchQuestion:
    require_keys(credentials)
    limiter = get_run_limiter()
    if not limiter.try_acquire():
        raise AppError(
            "Too many research runs were started. Wait a few minutes and try again.",
            status_code=429,
            code="rate_limited",
        )
    try:
        record = create_research_question(db, payload.question)
    except Exception:
        limiter.release()
        raise
    background.add_task(_run_and_release, run_research, record.id, credentials)
    return record


@router.get("/{question_id}", response_model=ResearchSessionRead)
def read_research_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ResearchSessionRead:
    return load_research_session(db, question_id)


@router.get("/{question_id}/graph", response_model=EvidenceGraphRead)
def read_evidence_graph(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> EvidenceGraphRead:
    return load_evidence_graph(db, question_id)


@router.post("/{question_id}/review", response_model=ResearchQuestionRead)
def review_question(
    question_id: uuid.UUID,
    payload: ReviewRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    resume=Depends(get_review_runner),
    credentials: Credentials = Depends(request_credentials),
) -> ResearchQuestion:
    record = get_research_question(db, question_id)
    if record.stage != "awaiting_review":
        raise AppError(
            "This run is not waiting for a review.",
            status_code=409,
            code="not_awaiting_review",
        )
    if payload.action == "continue":
        expected = claim_ids_for(db, record.id)
        decided = {item.claim_id for item in payload.decisions}
        if decided != expected:
            raise AppError(
                "Approve or reject every extracted claim before continuing.",
                status_code=422,
                code="validation_error",
            )
    require_keys(credentials)
    background.add_task(_resume_with_keys, resume, record.id, payload.model_dump(mode="json"), credentials)
    return record


@router.get("/{question_id}/export.md")
def export_markdown(question_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    session = load_research_session(db, question_id)
    return Response(
        content=render_markdown(session),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="prooflens-{question_id}.md"'},
    )


@router.get("/{question_id}/export.pdf")
def export_pdf(question_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    session = load_research_session(db, question_id)
    return Response(
        content=render_pdf(session),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="prooflens-{question_id}.pdf"'},
    )


@router.get("/{question_id}/events")
async def stream_activity(question_id: uuid.UUID, request: Request) -> StreamingResponse:
    exists = await asyncio.to_thread(_question_exists, question_id)
    if not exists:
        raise AppError(
            "No research question exists with that id.",
            status_code=404,
            code="not_found",
        )
    cursor = _event_cursor(request.headers.get("last-event-id"))
    return StreamingResponse(
        _activity_stream(str(question_id), cursor, request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _run_and_release(run, question_id: uuid.UUID, credentials: Credentials) -> None:
    token = use_credentials(credentials)
    try:
        run(question_id)
    finally:
        reset_credentials(token)
        get_run_limiter().release()


def _resume_with_keys(resume, question_id: uuid.UUID, decision: dict, credentials: Credentials) -> None:
    token = use_credentials(credentials)
    try:
        resume(question_id, decision)
    finally:
        reset_credentials(token)


def _question_exists(question_id: uuid.UUID) -> bool:
    db = SessionLocal()
    try:
        return db.get(ResearchQuestion, question_id) is not None
    finally:
        db.close()


def _event_cursor(header: str | None) -> int:
    if not header:
        return 0
    try:
        return max(int(header), 0)
    except ValueError:
        return 0


async def _activity_stream(session_id: str, cursor: int, request: Request):
    quiet = 0
    while True:
        if await request.is_disconnected():
            return
        batch = activity_log.since(session_id, cursor)
        if batch:
            quiet = 0
            for event in batch:
                cursor = event["id"]
                yield _sse(event)
            if batch[-1]["terminal"]:
                return
        else:
            quiet += 1
            if quiet % 15 == 0:
                yield ": keepalive\n\n"
            if quiet >= 900:
                return
        await asyncio.sleep(0.4)


def _sse(event: dict) -> str:
    payload = json.dumps(event)
    return f"id: {event['id']}\ndata: {payload}\n\n"
