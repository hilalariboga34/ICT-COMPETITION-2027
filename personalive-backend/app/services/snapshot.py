from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session as DBSession

from app.models.analysis_result import AnalysisResult as AnalysisResultModel
from app.repositories.analysis import AnalysisResultRepository
from app.repositories.participant import ParticipantRepository
from app.repositories.session import SessionRepository
from app.schemas.analysis import AnalysisResult as AnalysisResultResponse
from app.schemas.snapshot import SessionSnapshotParticipant, SessionSnapshotResponse
from app.services.participants import to_participant_response
from app.services.sessions import SessionNotFoundError, to_session_response


def to_analysis_result_response(result: AnalysisResultModel) -> AnalysisResultResponse:
    """Persistence modelinin snake_case alanlarını API sözleşmesine
    (camelCase) çevirir. modelVersion alanı, eager-load edilmiş
    model_version ilişkisinin 'name' kolonundan gelir — ayrı sorgu
    tetiklemez (bkz. AnalysisResultRepository.get_latest_by_session)."""
    return AnalysisResultResponse(
        sessionId=result.session_id,
        participantId=result.participant_id,
        realityScore=result.reality_score,
        confidence=result.confidence,
        status=result.status.value,
        timestamp=result.timestamp,
        modelVersion=result.model_version.name,
    )


class SnapshotService:
    def __init__(self, db_session: DBSession) -> None:
        self.db_session = db_session
        self.session_repository = SessionRepository(db_session)
        self.participant_repository = ParticipantRepository(db_session)
        self.analysis_repository = AnalysisResultRepository(db_session)

    def get_snapshot(self, session_id: UUID) -> SessionSnapshotResponse:
        # Salt okuma: lifecycle start/end'in aksine kilit gerekmiyor.
        session = self.session_repository.get_by_id(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        # list_by_session zaten joined_at ASC sıralı döner.
        participants = self.participant_repository.list_by_session(session_id)

        # Tek sorguda, session'daki her participant için en son analiz.
        # Session filtresi sayesinde başka session'ların analizleri hiç
        # gelmiyor (composite FK de bunu veri katmanında garanti ediyor).
        latest_analyses = self.analysis_repository.get_latest_by_session(session_id)
        latest_by_participant_id = {
            result.participant_id: result for result in latest_analyses
        }

        snapshot_participants = [
            SessionSnapshotParticipant(
                participant=to_participant_response(participant),
                latestAnalysis=(
                    to_analysis_result_response(
                        latest_by_participant_id[participant.id]
                    )
                    if participant.id in latest_by_participant_id
                    else None
                ),
            )
            for participant in participants
        ]

        return SessionSnapshotResponse(
            session=to_session_response(session),
            participants=snapshot_participants,
        )
