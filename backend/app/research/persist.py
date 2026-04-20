import uuid

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.research_question import COMPLETED, FAILED, RUNNING, ResearchQuestion
from app.models.results import (
    ClaimRecord,
    ContradictionRecord,
    ReportRecord,
    SourceRecord,
    VerificationRecord,
)


def save_progress(question_id: uuid.UUID, state: dict, finished: bool = False) -> None:
    db = SessionLocal()
    try:
        record = db.get(ResearchQuestion, question_id)
        if record is None:
            return
        _replace_children(db, question_id, state)
        status = _status(state, finished)
        record.status = status
        if status == COMPLETED:
            record.stage = "completed"
            record.error_message = None
        elif status == FAILED:
            record.stage = "failed"
            record.error_message = state.get("last_error") or "Research did not produce a report."
        else:
            record.stage = state.get("stage") or "researching"
            record.error_message = None
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _status(state: dict, finished: bool) -> str:
    if state.get("failed"):
        return FAILED
    if not finished:
        return RUNNING
    if state.get("report"):
        return COMPLETED
    return FAILED


def _replace_children(db, question_id: uuid.UUID, state: dict) -> None:
    claim_ids = select(ClaimRecord.id).where(ClaimRecord.research_question_id == question_id)
    db.execute(delete(VerificationRecord).where(VerificationRecord.claim_id.in_(claim_ids)))
    db.execute(delete(ContradictionRecord).where(ContradictionRecord.research_question_id == question_id))
    db.execute(delete(ClaimRecord).where(ClaimRecord.research_question_id == question_id))
    db.execute(delete(SourceRecord).where(SourceRecord.research_question_id == question_id))
    db.execute(delete(ReportRecord).where(ReportRecord.research_question_id == question_id))

    for position, source in enumerate(state.get("sources") or []):
        db.add(
            SourceRecord(
                research_question_id=question_id,
                position=position,
                url=source["url"],
                title=source.get("title") or source["url"],
                snippet=source.get("snippet") or "",
                content=source.get("content") or "",
                search_query=source.get("search_query") or "",
            )
        )

    for position, claim in enumerate(state.get("claims") or []):
        db.add(
            ClaimRecord(
                id=uuid.UUID(claim["id"]),
                research_question_id=question_id,
                position=position,
                source_url=claim["source_url"],
                text=claim["text"],
                kind=claim["kind"],
            )
        )

    db.flush()
    for verdict in state.get("verifications") or []:
        db.add(
            VerificationRecord(
                research_question_id=question_id,
                claim_id=uuid.UUID(verdict["claim_id"]),
                status=verdict["status"],
                explanation=verdict.get("explanation") or "",
                supporting_excerpt=verdict.get("supporting_excerpt") or "",
                opposing_excerpt=verdict.get("opposing_excerpt") or "",
            )
        )

    for item in state.get("contradictions") or []:
        db.add(
            ContradictionRecord(
                research_question_id=question_id,
                claim_id=uuid.UUID(item["claim_id"]),
                other_claim_id=uuid.UUID(item["other_claim_id"]),
                explanation=item["explanation"],
                context=item.get("context") or "",
            )
        )

    report = state.get("report")
    if report:
        db.add(
            ReportRecord(
                research_question_id=question_id,
                summary=report.get("summary") or "",
                findings=report.get("findings") or [],
                uncertainties=report.get("uncertainties") or [],
                limitations=report.get("limitations") or [],
            )
        )
