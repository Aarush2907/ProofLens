import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.research_question import SUBMITTED, ResearchQuestion
from app.services.questions import normalise_question


def create_research_question(db: Session, question: str) -> ResearchQuestion:
    record = ResearchQuestion(question=normalise_question(question), status=SUBMITTED)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_research_questions(db: Session, limit: int) -> list[ResearchQuestion]:
    statement = (
        select(ResearchQuestion)
        .order_by(ResearchQuestion.created_at.desc(), ResearchQuestion.id.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def get_research_question(db: Session, question_id: uuid.UUID) -> ResearchQuestion:
    record = db.get(ResearchQuestion, question_id)
    if record is None:
        raise AppError(
            "No research question exists with that id.",
            status_code=404,
            code="not_found",
        )
    return record
