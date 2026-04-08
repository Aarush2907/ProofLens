import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.research_question import ResearchQuestion
from app.schemas.research import ResearchQuestionCreate, ResearchQuestionRead
from app.services.research import (
    create_research_question,
    get_research_question,
    list_research_questions,
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
    db: Session = Depends(get_db),
) -> ResearchQuestion:
    return create_research_question(db, payload.question)


@router.get("/{question_id}", response_model=ResearchQuestionRead)
def read_research_question(
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> ResearchQuestion:
    return get_research_question(db, question_id)
