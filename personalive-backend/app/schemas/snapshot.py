from pydantic import BaseModel, ConfigDict, Field

from app.schemas.analysis import AnalysisResult
from app.schemas.participant import ParticipantResponse
from app.schemas.session import SessionResponse


class SessionSnapshotParticipant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    participant: ParticipantResponse = Field(...)
    # Participant'ın hiç analizi yoksa null döner.
    latestAnalysis: AnalysisResult | None = Field(...)


class SessionSnapshotResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: SessionResponse = Field(...)
    # joinedAt ASC sırasıyla — disconnected participant'lar da listede kalır.
    participants: list[SessionSnapshotParticipant] = Field(...)
