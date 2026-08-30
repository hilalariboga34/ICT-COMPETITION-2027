from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.analysis import AnalysisInput, AnalysisResult, ParticipantStatus


SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
PARTICIPANT_ID = UUID("22222222-2222-4222-8222-222222222222")
UTC_TIMESTAMP = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)


def valid_analysis_input_data() -> dict[str, object]:
    return {
        "sessionId": SESSION_ID,
        "participantId": PARTICIPANT_ID,
        "fakeProbability": 0.25,
        "confidence": 0.9,
        "timestamp": UTC_TIMESTAMP,
        "modelVersion": "analysis-v1",
    }


def test_valid_analysis_input_is_accepted() -> None:
    analysis_input = AnalysisInput(**valid_analysis_input_data())

    assert analysis_input.sessionId == SESSION_ID


def test_fake_probability_above_one_is_rejected() -> None:
    data = valid_analysis_input_data()
    data["fakeProbability"] = 1.01

    with pytest.raises(ValidationError):
        AnalysisInput(**data)


def test_confidence_below_zero_is_rejected() -> None:
    data = valid_analysis_input_data()
    data["confidence"] = -0.01

    with pytest.raises(ValidationError):
        AnalysisInput(**data)


def test_timestamp_without_timezone_is_rejected() -> None:
    data = valid_analysis_input_data()
    data["timestamp"] = datetime(2026, 1, 15, 12, 30)

    with pytest.raises(ValidationError):
        AnalysisInput(**data)


def test_extra_field_is_rejected() -> None:
    data = valid_analysis_input_data()
    data["unexpectedField"] = "unexpected"

    with pytest.raises(ValidationError):
        AnalysisInput(**data)


def test_analysis_result_with_valid_status_is_accepted() -> None:
    result = AnalysisResult(
        sessionId=SESSION_ID,
        participantId=PARTICIPANT_ID,
        realityScore=0.8,
        confidence=0.95,
        status=ParticipantStatus.AUTHENTIC,
        timestamp=UTC_TIMESTAMP,
        modelVersion="analysis-v1",
    )

    assert result.status is ParticipantStatus.AUTHENTIC


def test_analysis_result_with_invalid_status_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult(
            sessionId=SESSION_ID,
            participantId=PARTICIPANT_ID,
            realityScore=0.8,
            confidence=0.95,
            status="invalid",
            timestamp=UTC_TIMESTAMP,
            modelVersion="analysis-v1",
        )


def test_empty_model_version_is_rejected() -> None:
    data = valid_analysis_input_data()
    data["modelVersion"] = ""

    with pytest.raises(ValidationError):
        AnalysisInput(**data)
