import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

SUBMITTED = "submitted"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchQuestion(Base):
    """A question saved from the research desk.

    Milestone 1 stores the question and marks it submitted. It does not store
    sources, claims, or a report, because none of those are produced yet.
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
