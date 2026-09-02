from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session as DBSession

from app.models.session import Session as SessionModel
from app.repositories.session import SessionRepository
from app.schemas.session import SessionCreate, SessionResponse


def to_session_response(session: SessionModel) -> SessionResponse:
    """Map the persistence model's snake_case fields to the API contract."""
    return SessionResponse(
        sessionId=session.id,
        title=session.title,
        status=session.status.value,
        createdAt=session.created_at,
        startedAt=session.started_at,
        endedAt=session.ended_at,
    )


class SessionService:
    def __init__(self, db_session: DBSession) -> None:
        self.db_session = db_session
        self.repository = SessionRepository(db_session)

    def create(self, data: SessionCreate) -> SessionResponse:
        try:
            session = self.repository.create(title=data.title)
            response = to_session_response(session)
            self.db_session.commit()
            return response
        except Exception:
            self.db_session.rollback()
            raise

    def get_by_id(self, session_id: UUID) -> SessionResponse | None:
        session = self.repository.get_by_id(session_id)
        if session is None:
            return None
        return to_session_response(session)
