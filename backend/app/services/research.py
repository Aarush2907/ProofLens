import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.research_question import RUNNING, ResearchQuestion
from app.models.results import (
    ClaimRecord,
    ContradictionRecord,
    ReportRecord,
    SourceRecord,
    VerificationRecord,
)
from app.schemas.research import (
    ClaimRead,
    ContradictionRead,
    ReportRead,
    ResearchQuestionRead,
    ResearchSessionRead,
    SourceRead,
    VerificationRead,
)
from app.services.questions import normalise_question


def create_research_question(db: Session, question: str) -> ResearchQuestion:
    record = ResearchQuestion(
        question=normalise_question(question),
        status=RUNNING,
        stage="researching",
    )
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


def get_research_runner():
    from app.research.runner import execute_research

    return execute_research


def load_research_session(db: Session, question_id: uuid.UUID) -> ResearchSessionRead:
    record = get_research_question(db, question_id)
    sources = list(
        db.scalars(
            select(SourceRecord)
            .where(SourceRecord.research_question_id == record.id)
            .order_by(SourceRecord.position)
        ).all()
    )
    claims = list(
        db.scalars(
            select(ClaimRecord)
            .where(ClaimRecord.research_question_id == record.id)
            .order_by(ClaimRecord.position)
        ).all()
    )
    verifications = {
        item.claim_id: item
        for item in db.scalars(
            select(VerificationRecord).where(VerificationRecord.research_question_id == record.id)
        ).all()
    }
    claims_by_id = {claim.id: claim for claim in claims}
    contradictions = []
    for item in db.scalars(
        select(ContradictionRecord)
        .where(ContradictionRecord.research_question_id == record.id)
        .order_by(ContradictionRecord.explanation)
    ).all():
        first = claims_by_id.get(item.claim_id)
        second = claims_by_id.get(item.other_claim_id)
        if first is None or second is None:
            continue
        contradictions.append(
            ContradictionRead(
                explanation=item.explanation,
                context=item.context,
                claim_text=first.text,
                other_claim_text=second.text,
                source_url=first.source_url,
                other_source_url=second.source_url,
            )
        )

    report_row = db.scalar(
        select(ReportRecord).where(ReportRecord.research_question_id == record.id)
    )
    report = None
    if report_row is not None:
        report = ReportRead(
            summary=report_row.summary,
            findings=report_row.findings or [],
            uncertainties=report_row.uncertainties or [],
            limitations=report_row.limitations or [],
        )

    summary = ResearchQuestionRead.model_validate(record)
    return ResearchSessionRead(
        **summary.model_dump(),
        sources=[SourceRead.model_validate(source) for source in sources],
        claims=[
            ClaimRead(
                id=claim.id,
                source_url=claim.source_url,
                text=claim.text,
                kind=claim.kind,
                verification=(
                    VerificationRead.model_validate(verifications[claim.id])
                    if claim.id in verifications
                    else None
                ),
            )
            for claim in claims
        ],
        contradictions=contradictions,
        report=report,
    )
