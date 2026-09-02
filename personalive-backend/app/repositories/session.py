from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session as DBSession

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
