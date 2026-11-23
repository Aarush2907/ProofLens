import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.research_question import COMPLETED, FAILED, RUNNING, ResearchQuestion
from app.models.results import (
    ClaimRecord,
    ContradictionRecord,
    EvidenceRecord,
    ReportRecord,
    SourceRecord,
    VerificationRecord,
)
from app.research.evidence import evidence_for
from app.research.usage import current_usage, estimate_cost, usage_is_active


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
        if usage_is_active():
            usage = current_usage()
            record.prompt_tokens = usage.prompt_tokens
            record.completion_tokens = usage.completion_tokens
            record.estimated_cost_usd = estimate_cost(usage.prompt_tokens, usage.completion_tokens)
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
    db.execute(delete(EvidenceRecord).where(EvidenceRecord.research_question_id == question_id))
    db.execute(delete(VerificationRecord).where(VerificationRecord.claim_id.in_(claim_ids)))
    db.execute(delete(ContradictionRecord).where(ContradictionRecord.research_question_id == question_id))
    db.execute(delete(ClaimRecord).where(ClaimRecord.research_question_id == question_id))
    db.execute(delete(SourceRecord).where(SourceRecord.research_question_id == question_id))
    db.execute(delete(ReportRecord).where(ReportRecord.research_question_id == question_id))

    for position, source in enumerate(state.get("sources") or []):
        db.add(
            SourceRecord(
                id=_uuid(source.get("id")),
                research_question_id=question_id,
                position=position,
                url=source["url"],
                title=source.get("title") or source["url"],
                domain=source.get("domain") or "",
                snippet=source.get("snippet") or "",
                content=source.get("content") or "",
                search_query=source.get("search_query") or "",
                author=source.get("author") or "",
                published_on=source.get("published_on") or "",
                retrieved_at=_timestamp(source.get("retrieved_at")),
            )
        )
    db.flush()

    for position, claim in enumerate(state.get("claims") or []):
        db.add(
            ClaimRecord(
                id=_uuid(claim["id"]),
                research_question_id=question_id,
                position=position,
                source_id=_optional_uuid(claim.get("source_id")),
                source_url=claim["source_url"],
                text=claim["text"],
                kind=claim["kind"],
                review_status=claim.get("review_status") or "pending",
            )
        )

    db.flush()
    for item in evidence_for(state.get("claims") or [], state.get("verifications") or []):
        db.add(
            EvidenceRecord(
                research_question_id=question_id,
                claim_id=_uuid(item["claim_id"]),
                source_id=_optional_uuid(item.get("source_id")),
                source_url=item["source_url"],
                stance=item["stance"],
                passage=item["passage"],
            )
        )
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


def _uuid(value) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def _optional_uuid(value) -> uuid.UUID | None:
    if not value:
        return None
    return _uuid(value)


def _timestamp(value):
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
