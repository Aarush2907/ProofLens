import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.research_question import ResearchQuestion
from app.schemas.research import ResearchQuestionCreate, ResearchQuestionRead, ResearchSessionRead
from app.services.research import (
    create_research_question,
    get_research_runner,
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
