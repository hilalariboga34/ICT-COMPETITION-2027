from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.analysis_result import AnalysisResult
from app.models.enums import ParticipantStatus


class AnalysisResultRepository:
    def __init__(self, db_session: DBSession) -> None:
        self.db_session = db_session

    def get_latest_timestamp(self, participant_id: UUID) -> datetime | None:
        statement = (
            select(AnalysisResult.timestamp)
            .where(AnalysisResult.participant_id == participant_id)
            .order_by(AnalysisResult.timestamp.desc())
            .limit(1)
        )
        return self.db_session.execute(statement).scalar_one_or_none()

    def create(
        self,
        *,
        session_id: UUID,
        participant_id: UUID,
        model_version_id: int,
        reality_score: float,
        confidence: float,
        status: ParticipantStatus,
        timestamp: datetime,
    ) -> AnalysisResult:
        result = AnalysisResult(
            session_id=session_id,
            participant_id=participant_id,
            model_version_id=model_version_id,
            reality_score=reality_score,
            confidence=confidence,
            status=status,
            timestamp=timestamp,
        )
        self.db_session.add(result)
        self.db_session.flush()
        return result
