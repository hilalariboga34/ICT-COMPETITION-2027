from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session as DBSession

from app.models.enums import ParticipantStatus
from app.models.participant import Participant
from app.repositories.participant import ParticipantRepository
from app.repositories.session import SessionRepository
from app.schemas.participant import ParticipantCreate, ParticipantResponse


class SessionNotFoundError(Exception):
    """İşlem yapılmak istenen session_id veritabanında yok."""


class ParticipantNotFoundError(Exception):
    """participant_id, belirtilen session'da bulunamadı — ya hiç yok ya da
    başka bir session'a ait (bu ikisi API açısından aynı 404 sonucu)."""


def to_participant_response(participant: Participant) -> ParticipantResponse:
    """Persistence modelinin snake_case alanlarını API sözleşmesine (camelCase) çevirir."""
    return ParticipantResponse(
        participantId=participant.id,
        sessionId=participant.session_id,
        displayName=participant.display_name,
        status=ParticipantStatus(participant.status),
        joinedAt=participant.joined_at,
        leftAt=participant.left_at,
    )


class ParticipantService:
    def __init__(self, db_session: DBSession) -> None:
        self.db_session = db_session
        self.repository = ParticipantRepository(db_session)
        self.session_repository = SessionRepository(db_session)

    def create(
        self, session_id: UUID, data: ParticipantCreate
    ) -> ParticipantResponse:
        try:
            if self.session_repository.get_by_id(session_id) is None:
                raise SessionNotFoundError(session_id)

            participant = self.repository.create(
                session_id=session_id, display_name=data.displayName
            )
            response = to_participant_response(participant)
            self.db_session.commit()
            return response
        except Exception:
            self.db_session.rollback()
            raise

    def list_by_session(self, session_id: UUID) -> list[ParticipantResponse]:
        if self.session_repository.get_by_id(session_id) is None:
            raise SessionNotFoundError(session_id)

        participants = self.repository.list_by_session(session_id)
        return [to_participant_response(participant) for participant in participants]

    def disconnect(
        self, session_id: UUID, participant_id: UUID
    ) -> ParticipantResponse:
        try:
            if self.session_repository.get_by_id(session_id) is None:
                raise SessionNotFoundError(session_id)

            participant = self.repository.get_by_id_and_session(
                participant_id, session_id
            )
            if participant is None:
                raise ParticipantNotFoundError(participant_id)

            # Idempotent: zaten disconnected ise left_at'e dokunmadan,
            # hata vermeden mevcut kaydı olduğu gibi döndür.
            if participant.status != ParticipantStatus.DISCONNECTED:
                participant = self.repository.mark_disconnected(
                    participant, left_at=datetime.now(timezone.utc)
                )

            response = to_participant_response(participant)
            self.db_session.commit()
            return response
        except Exception:
            self.db_session.rollback()
            raise
