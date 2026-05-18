import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
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
) -> ResearchQuestion:
    record = create_research_question(db, payload.question)
    background.add_task(run_research, record.id)
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
    background.add_task(resume, record.id, payload.model_dump(mode="json"))
    return record
