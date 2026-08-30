from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SessionStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    ENDED = "ended"


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sessionId: UUID = Field(...)
    title: str = Field(..., min_length=1, max_length=200)
    status: SessionStatus = Field(...)
    createdAt: datetime = Field(...)
    startedAt: datetime | None = Field(...)
    endedAt: datetime | None = Field(...)

    @field_validator("createdAt", "startedAt", "endedAt")
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
