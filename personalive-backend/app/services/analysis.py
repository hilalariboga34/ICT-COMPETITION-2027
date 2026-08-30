from app.schemas.analysis import AnalysisInput, AnalysisResult, ParticipantStatus


DEFAULT_AUTHENTIC_THRESHOLD = 0.60


def build_analysis_result(
    analysis_input: AnalysisInput,
    authentic_threshold: float = DEFAULT_AUTHENTIC_THRESHOLD,
) -> AnalysisResult:
    if not 0.0 <= authentic_threshold <= 1.0:
        raise ValueError("authentic_threshold must be between 0.0 and 1.0")

    reality_score = 1.0 - analysis_input.fakeProbability
    status = (
        ParticipantStatus.AUTHENTIC
        if reality_score >= authentic_threshold
        else ParticipantStatus.SUSPICIOUS
    )

    return AnalysisResult(
        sessionId=analysis_input.sessionId,
        participantId=analysis_input.participantId,
        realityScore=reality_score,
        confidence=analysis_input.confidence,
        status=status,
        timestamp=analysis_input.timestamp,
        modelVersion=analysis_input.modelVersion,
    )
