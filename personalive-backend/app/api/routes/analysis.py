from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession

from app.core.config import get_settings
from app.db.session import get_db_session
from app.realtime.manager import connection_manager
from app.schemas.analysis import AnalysisInput, AnalysisResult
from app.schemas.events import AnalysisUpdatedEvent
from app.services.analysis import (
    AnalysisService,
    ParticipantDisconnectedError,
    ParticipantNotFoundError,
    SessionNotFoundError,
    StaleAnalysisTimestampError,
)


settings = get_settings()

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/evaluate", response_model=AnalysisResult, status_code=200)
async def evaluate_analysis(
    analysis_input: AnalysisInput,
    db_session: DBSession = Depends(get_db_session),
) -> AnalysisResult:
    try:
        result = AnalysisService(db_session).evaluate(
            analysis_input,
            authentic_threshold=settings.authentic_threshold,
        )
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        ) from exc
    except ParticipantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found"
        ) from exc
    except ParticipantDisconnectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Participant is disconnected",
        ) from exc
    except StaleAnalysisTimestampError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis timestamp must be newer than the latest analysis",
        ) from exc

    event = AnalysisUpdatedEvent(type="analysis.updated", data=result)
    await connection_manager.broadcast_analysis(result.sessionId, event)
    return result
