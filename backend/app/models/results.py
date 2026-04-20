import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.research_question import utc_now


class SourceRecord(Base):
    __tablename__ = "research_sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("research_questions.id"),
        index=True,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    search_query: Mapped[str] = mapped_column(Text, nullable=False, default="")


class ClaimRecord(Base):
    __tablename__ = "research_claims"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("research_questions.id"),
        index=True,
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)


class VerificationRecord(Base):
    __tablename__ = "research_verifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("research_questions.id"),
        index=True,
        nullable=False,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("research_claims.id"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    supporting_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    opposing_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")


class ContradictionRecord(Base):
    __tablename__ = "research_contradictions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("research_questions.id"),
        index=True,
        nullable=False,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    other_claim_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=False, default="")


class ReportRecord(Base):
    __tablename__ = "research_reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    research_question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("research_questions.id"),
        unique=True,
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    findings: Mapped[list] = mapped_column(JSON, nullable=False)
    uncertainties: Mapped[list] = mapped_column(JSON, nullable=False)
    limitations: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=utc_now)
