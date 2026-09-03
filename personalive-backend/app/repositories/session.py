from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session as DBSession

from app.models.enums import SessionStatus
from app.models.session import Session as SessionModel


class SessionRepository:
    def __init__(self, db_session: DBSession) -> None:
        self.db_session = db_session

    def create(self, title: str) -> SessionModel:
        session = SessionModel(title=title)
        self.db_session.add(session)
        self.db_session.flush()
        self.db_session.refresh(session)
        return session

    def get_by_id(self, session_id: UUID) -> SessionModel | None:
        return self.db_session.get(SessionModel, session_id)

    def start(self, session: SessionModel, *, started_at: datetime) -> SessionModel:
        session.status = SessionStatus.ACTIVE
        session.started_at = started_at
        self.db_session.flush()
        self.db_session.refresh(session)
        return session

    def end(self, session: SessionModel, *, ended_at: datetime) -> SessionModel:
        session.status = SessionStatus.ENDED
        session.ended_at = ended_at
        self.db_session.flush()
        self.db_session.refresh(session)
        return session
