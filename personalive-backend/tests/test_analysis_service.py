from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.schemas.analysis import AnalysisInput, ParticipantStatus
from app.services.analysis import build_analysis_result


SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
PARTICIPANT_ID = UUID("22222222-2222-4222-8222-222222222222")
UTC_TIMESTAMP = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)


def make_analysis_input(fake_probability: float = 0.25) -> AnalysisInput:
    return AnalysisInput(
        sessionId=SESSION_ID,
        participantId=PARTICIPANT_ID,
        fakeProbability=fake_probability,
        confidence=0.9,
        timestamp=UTC_TIMESTAMP,
        modelVersion="analysis-v1",
    )


def test_reality_score_is_one_minus_fake_probability() -> None:
    result = build_analysis_result(make_analysis_input(fake_probability=0.25))

    assert result.realityScore == pytest.approx(0.75)


def test_common_input_fields_are_preserved() -> None:
    analysis_input = make_analysis_input()

    result = build_analysis_result(analysis_input)

    assert result.sessionId == analysis_input.sessionId
    assert result.participantId == analysis_input.participantId
    assert result.confidence == pytest.approx(analysis_input.confidence)
    assert result.timestamp == analysis_input.timestamp
    assert result.modelVersion == analysis_input.modelVersion


def test_score_above_default_threshold_is_authentic() -> None:
    result = build_analysis_result(make_analysis_input(fake_probability=0.39))

    assert result.status is ParticipantStatus.AUTHENTIC


def test_score_equal_to_default_threshold_is_authentic() -> None:
    result = build_analysis_result(make_analysis_input(fake_probability=0.40))

    assert result.status is ParticipantStatus.AUTHENTIC


def test_score_below_default_threshold_is_suspicious() -> None:
    result = build_analysis_result(make_analysis_input(fake_probability=0.41))

    assert result.status is ParticipantStatus.SUSPICIOUS


def test_custom_authentic_threshold_is_used() -> None:
    result = build_analysis_result(
        make_analysis_input(fake_probability=0.25),
        authentic_threshold=0.80,
    )

    assert result.status is ParticipantStatus.SUSPICIOUS


def test_threshold_below_zero_raises_value_error() -> None:
    with pytest.raises(ValueError):
        build_analysis_result(make_analysis_input(), authentic_threshold=-0.01)


def test_threshold_above_one_raises_value_error() -> None:
    with pytest.raises(ValueError):
        build_analysis_result(make_analysis_input(), authentic_threshold=1.01)
