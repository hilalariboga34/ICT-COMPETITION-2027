from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session as DBSession

from app.models.enums import ParticipantStatus, SessionStatus
from app.models.session import Session as SessionModel
from app.repositories.participant import ParticipantRepository
from app.repositories.session import SessionRepository
from app.schemas.session import SessionCreate, SessionResponse


class SessionNotFoundError(Exception):
    """İşlem yapılmak istenen session_id veritabanında yok."""


class InvalidSessionTransitionError(Exception):
    """Session'ın mevcut durumundan istenen duruma geçiş kurallara aykırı
    (örn. zaten active olan bir session'ı tekrar başlatmaya çalışmak,
    ya da hiç başlamamış bir session'ı bitirmeye çalışmak)."""


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
        self.participant_repository = ParticipantRepository(db_session)

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

    def start(self, session_id: UUID) -> SessionResponse:
        try:
            # for_update=True: eşzamanlı iki start isteğinin ikisinin de
            # aynı waiting status'u okuyup ikisinin de geçişi geçerli
            # sanmasını (race condition) engellemek için satırı kilitler.
            session = self.repository.get_by_id(session_id, for_update=True)
            if session is None:
                raise SessionNotFoundError(session_id)

            # Yalnızca waiting -> active geçişi geçerli. Zaten active ya da
            # ended olan bir session'ı tekrar başlatmak geçersiz bir geçiş
            # sayılır (idempotent değil, her çağrı gerçek bir durum kontrolü
            # yapar) — bu yüzden ikinci start çağrısı da 409 döner.
            if session.status != SessionStatus.WAITING:
                raise InvalidSessionTransitionError(session_id)

            session = self.repository.start(
                session, started_at=datetime.now(timezone.utc)
            )
            response = to_session_response(session)
            self.db_session.commit()
            return response
        except Exception:
            self.db_session.rollback()
            raise

    def end(self, session_id: UUID) -> SessionResponse:
        try:
            # for_update=True: eşzamanlı iki end isteğinin (ya da bir end ile
            # çakışan bir start'ın) aynı active status'u okuyup ikisinin de
            # geçişi geçerli sanmasını (race condition) engellemek için
            # satırı kilitler.
            session = self.repository.get_by_id(session_id, for_update=True)
            if session is None:
                raise SessionNotFoundError(session_id)

            # Yalnızca active -> ended geçişi geçerli. waiting (hiç
            # başlamamış) ya da zaten ended olan bir session'ı bitirmeye
            # çalışmak geçersiz bir geçiş sayılır -> 409.
            if session.status != SessionStatus.ACTIVE:
                raise InvalidSessionTransitionError(session_id)

            ended_at = datetime.now(timezone.utc)
            session = self.repository.end(session, ended_at=ended_at)

            # Session sona erdiğinde hâlâ aktif (disconnected olmayan)
            # participant'lar disconnect edilir, left_at aynı ended_at ile
            # doldurulur. Zaten disconnected olanlara dokunulmaz (mevcut
            # left_at'leri korunur).
            participants = self.participant_repository.list_by_session(session_id)
            for participant in participants:
                if participant.status != ParticipantStatus.DISCONNECTED:
                    self.participant_repository.mark_disconnected(
                        participant, left_at=ended_at
                    )

            response = to_session_response(session)
            self.db_session.commit()
            return response
        except Exception:
            self.db_session.rollback()
            raise
