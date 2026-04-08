import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.services.questions import normalise_question


class ResearchQuestionCreate(BaseModel):
    question: str = Field(max_length=4000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        return normalise_question(value)


class ResearchQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_timestamp(self, value: datetime) -> str:
        # SQLite drops timezone information. Stored values are UTC.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
