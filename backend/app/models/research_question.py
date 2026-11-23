import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

SUBMITTED = "submitted"
RUNNING = "running"
COMPLETED = "completed"
FAILED = "failed"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchQuestion(Base):
    """A question from the research desk and the status of its run.

    Sources, claims, checks, contradictions, and the report live in their own
    tables. This row only records where the run is.
    """

    __tablename__ = "research_questions"
    __table_args__ = (
        CheckConstraint(
            "length(trim(question)) > 0",
            name="ck_research_questions_question_not_blank",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=SUBMITTED)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default=SUBMITTED)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )
