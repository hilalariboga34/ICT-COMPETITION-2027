from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession, joinedload

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

    def get_latest_by_session(self, session_id: UUID) -> list[AnalysisResult]:
        """Bir session'daki her participant için EN SON analiz sonucunu tek
        sorguda döner (N+1 yok). PostgreSQL'e özgü DISTINCT ON kullanır:
        participant_id'ye göre gruplar, her grupta timestamp'e göre en
        yeniyi seçer. session_id filtresi, başka bir session'a ait
        analizlerin asla karışmamasını garanti eder (composite FK zaten bunu
        veri katmanında da garanti ediyor). model_version ilişkisi
        joinedload ile eager-load edilir, ayrı sorgu tetiklemez."""
        statement = (
            select(AnalysisResult)
            .where(AnalysisResult.session_id == session_id)
            .distinct(AnalysisResult.participant_id)
            .order_by(AnalysisResult.participant_id, AnalysisResult.timestamp.desc())
            .options(joinedload(AnalysisResult.model_version))
        )
        return list(self.db_session.execute(statement).scalars().all())

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
