from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.models.enums import ParticipantStatus
from app.models.participant import Participant


class ParticipantRepository:
    def __init__(self, db_session: DBSession) -> None:
        self.db_session = db_session

    def create(self, session_id: UUID, display_name: str) -> Participant:
        participant = Participant(session_id=session_id, display_name=display_name)
        self.db_session.add(participant)
        self.db_session.flush()
        self.db_session.refresh(participant)
        return participant

    def list_by_session(self, session_id: UUID) -> list[Participant]:
        statement = (
            select(Participant)
            .where(Participant.session_id == session_id)
            .order_by(Participant.joined_at)
        )
        return list(self.db_session.execute(statement).scalars().all())

    def get_by_id_and_session(
        self,
        participant_id: UUID,
        session_id: UUID,
        *,
        for_update: bool = False,
    ) -> Participant | None:
        # session_id'yi de filtreye dahil ediyoruz ki başka bir session'a ait
        # bir participant_id, yanlışlıkla bu session'a aitmiş gibi bulunmasın.
        statement = select(Participant).where(
            Participant.id == participant_id,
            Participant.session_id == session_id,
        )
        if for_update:
            statement = statement.with_for_update()
        return self.db_session.execute(statement).scalar_one_or_none()

    def update_status(
        self, participant: Participant, status: ParticipantStatus
    ) -> Participant:
        participant.status = status
        return participant

    def mark_disconnected(
        self, participant: Participant, *, left_at: datetime
    ) -> Participant:
        participant.status = ParticipantStatus.DISCONNECTED
        participant.left_at = left_at
        self.db_session.flush()
        self.db_session.refresh(participant)
        return participant
