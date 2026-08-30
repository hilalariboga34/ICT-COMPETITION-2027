from fastapi import APIRouter

from app.schemas.analysis import AnalysisInput, AnalysisResult
from app.services.analysis import build_analysis_result


router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.post("/evaluate", response_model=AnalysisResult, status_code=200)
def evaluate_analysis(analysis_input: AnalysisInput) -> AnalysisResult:
    return build_analysis_result(analysis_input)
