from sqlalchemy.orm import Session as DBSession

from app.models.enums import ParticipantStatus as ModelParticipantStatus
from app.repositories.analysis import AnalysisResultRepository
from app.repositories.model_version import ModelVersionRepository
from app.repositories.participant import ParticipantRepository
from app.repositories.session import SessionRepository
from app.schemas.analysis import AnalysisInput, AnalysisResult, ParticipantStatus


DEFAULT_AUTHENTIC_THRESHOLD = 0.60


class SessionNotFoundError(Exception):
    pass


class ParticipantNotFoundError(Exception):
    pass


class ParticipantDisconnectedError(Exception):
    pass


class StaleAnalysisTimestampError(Exception):
    pass


def build_analysis_result(
    analysis_input: AnalysisInput,
    authentic_threshold: float = DEFAULT_AUTHENTIC_THRESHOLD,
) -> AnalysisResult:
    if not 0.0 <= authentic_threshold <= 1.0:
        raise ValueError("authentic_threshold must be between 0.0 and 1.0")

    reality_score = 1.0 - analysis_input.fakeProbability
    status = (
        ParticipantStatus.AUTHENTIC
        if reality_score >= authentic_threshold
        else ParticipantStatus.SUSPICIOUS
    )

    return AnalysisResult(
        sessionId=analysis_input.sessionId,
        participantId=analysis_input.participantId,
        realityScore=reality_score,
        confidence=analysis_input.confidence,
        status=status,
        timestamp=analysis_input.timestamp,
        modelVersion=analysis_input.modelVersion,
    )


class AnalysisService:
    def __init__(self, db_session: DBSession) -> None:
        self.db_session = db_session
        self.analysis_repository = AnalysisResultRepository(db_session)
        self.model_version_repository = ModelVersionRepository(db_session)
        self.participant_repository = ParticipantRepository(db_session)
        self.session_repository = SessionRepository(db_session)

    def evaluate(
        self,
        analysis_input: AnalysisInput,
        *,
        authentic_threshold: float = DEFAULT_AUTHENTIC_THRESHOLD,
    ) -> AnalysisResult:
        try:
            if self.session_repository.get_by_id(analysis_input.sessionId) is None:
                raise SessionNotFoundError(analysis_input.sessionId)

            # Locking the participant serializes timestamp checks and inserts for
            # concurrent analyses belonging to the same participant.
            participant = self.participant_repository.get_by_id_and_session(
                analysis_input.participantId,
                analysis_input.sessionId,
                for_update=True,
            )
            if participant is None:
                raise ParticipantNotFoundError(analysis_input.participantId)
            if participant.status == ModelParticipantStatus.DISCONNECTED:
                raise ParticipantDisconnectedError(analysis_input.participantId)

            latest_timestamp = self.analysis_repository.get_latest_timestamp(
                participant.id
            )
            if (
                latest_timestamp is not None
                and analysis_input.timestamp <= latest_timestamp
            ):
                raise StaleAnalysisTimestampError(analysis_input.timestamp)

            result = build_analysis_result(
                analysis_input,
                authentic_threshold=authentic_threshold,
            )
            persisted_status = ModelParticipantStatus(result.status.value)
            model_version = self.model_version_repository.get_or_create(
                result.modelVersion
            )
            self.analysis_repository.create(
                session_id=result.sessionId,
                participant_id=result.participantId,
                model_version_id=model_version.id,
                reality_score=result.realityScore,
                confidence=result.confidence,
                status=persisted_status,
                timestamp=result.timestamp,
            )
            self.participant_repository.update_status(participant, persisted_status)

            # The API response is a detached Pydantic value object and is fully
            # prepared before commit, so no expired ORM state is read afterward.
            response = result.model_copy(deep=True)
            self.db_session.commit()
            return response
        except Exception:
            self.db_session.rollback()
            raise
