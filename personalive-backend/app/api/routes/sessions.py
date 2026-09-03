from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db_session
from app.schemas.session import SessionCreate, SessionResponse
from app.services.sessions import (
    InvalidSessionTransitionError,
    SessionNotFoundError,
    SessionService,
)


router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    data: SessionCreate,
    db_session: DBSession = Depends(get_db_session),
) -> SessionResponse:
    return SessionService(db_session).create(data)


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    db_session: DBSession = Depends(get_db_session),
) -> SessionResponse:
    session = SessionService(db_session).get_by_id(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    return session


@router.post("/{session_id}/start", response_model=SessionResponse)
def start_session(
    session_id: UUID,
    db_session: DBSession = Depends(get_db_session),
) -> SessionResponse:
    try:
        return SessionService(db_session).start(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from exc
    except InvalidSessionTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session cannot be started from its current status",
        ) from exc


@router.post("/{session_id}/end", response_model=SessionResponse)
def end_session(
    session_id: UUID,
    db_session: DBSession = Depends(get_db_session),
) -> SessionResponse:
    try:
        return SessionService(db_session).end(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from exc
    except InvalidSessionTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session cannot be ended from its current status",
        ) from exc
