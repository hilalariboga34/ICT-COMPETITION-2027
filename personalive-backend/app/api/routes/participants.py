from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db_session
from app.schemas.participant import ParticipantCreate, ParticipantResponse
from app.services.participants import (
    ParticipantNotFoundError,
    ParticipantService,
    SessionNotFoundError,
)


router = APIRouter(
    prefix="/api/v1/sessions/{session_id}/participants", tags=["participants"]
)


@router.post("", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
def create_participant(
    session_id: UUID,
    data: ParticipantCreate,
    db_session: DBSession = Depends(get_db_session),
) -> ParticipantResponse:
    try:
        return ParticipantService(db_session).create(session_id, data)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from exc


@router.get("", response_model=list[ParticipantResponse])
def list_participants(
    session_id: UUID,
    db_session: DBSession = Depends(get_db_session),
) -> list[ParticipantResponse]:
    try:
        return ParticipantService(db_session).list_by_session(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from exc


@router.post(
    "/{participant_id}/disconnect",
    response_model=ParticipantResponse,
    status_code=status.HTTP_200_OK,
)
def disconnect_participant(
    session_id: UUID,
    participant_id: UUID,
    db_session: DBSession = Depends(get_db_session),
) -> ParticipantResponse:
    try:
        return ParticipantService(db_session).disconnect(session_id, participant_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from exc
    except ParticipantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
        ) from exc
