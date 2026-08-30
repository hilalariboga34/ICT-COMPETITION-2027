from fastapi import APIRouter

from app.core.config import get_settings
from app.realtime.manager import connection_manager
from app.schemas.analysis import AnalysisInput, AnalysisResult
from app.schemas.events import AnalysisUpdatedEvent
from app.services.analysis import build_analysis_result


settings = get_settings()

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/evaluate", response_model=AnalysisResult, status_code=200)
async def evaluate_analysis(analysis_input: AnalysisInput) -> AnalysisResult:
    result = build_analysis_result(
        analysis_input,
        authentic_threshold=settings.authentic_threshold,
    )
    event = AnalysisUpdatedEvent(type="analysis.updated", data=result)
    await connection_manager.broadcast_analysis(result.sessionId, event)
    return result
