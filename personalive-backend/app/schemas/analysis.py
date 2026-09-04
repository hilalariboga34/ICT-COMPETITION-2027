from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ParticipantStatus(str, Enum):
    ANALYZING = "analyzing"
    AUTHENTIC = "authentic"
    SUSPICIOUS = "suspicious"
    DISCONNECTED = "disconnected"


class AnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sessionId: UUID = Field(...)
    participantId: UUID = Field(...)
    fakeProbability: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(...)
    modelVersion: str = Field(..., min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_timestamp_timezone(self) -> Self:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
        return self


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sessionId: UUID = Field(...)
    participantId: UUID = Field(...)
    realityScore: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: ParticipantStatus = Field(...)
    timestamp: datetime = Field(...)
    modelVersion: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_timestamp_timezone(self) -> Self:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must include timezone information")
        return self
