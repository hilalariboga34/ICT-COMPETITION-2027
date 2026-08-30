from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.analysis import ParticipantStatus


class ParticipantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    displayName: str = Field(..., min_length=1, max_length=100)

    @field_validator("displayName", mode="before")
    @classmethod
    def strip_display_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    participantId: UUID = Field(...)
    sessionId: UUID = Field(...)
    displayName: str = Field(..., min_length=1, max_length=100)
    status: ParticipantStatus = Field(...)
    joinedAt: datetime = Field(...)
    leftAt: datetime | None = Field(...)

    @field_validator("joinedAt", "leftAt")
    @classmethod
    def validate_datetime_timezone(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        if value is not None and (
            value.tzinfo is None or value.utcoffset() is None
        ):
            raise ValueError("datetime values must include timezone information")
        return value
