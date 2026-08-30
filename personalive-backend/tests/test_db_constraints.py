"""FK, CHECK ve UNIQUE kısıtlarının gerçekten reddettiğini doğrular.
Gerçek local PostgreSQL gerektirir (bkz. conftest.requires_db)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    AnalysisResult,
    DatasetVideo,
    FaceSample,
    ManipulationMethod,
    ModelVersion,
    Participant,
)
from app.models import Session as SessionModel
from app.models.enums import ParticipantStatus
from tests.conftest import requires_db


@requires_db
def test_participant_with_unknown_session_is_rejected(db_session) -> None:
    fake_session_id = uuid.uuid4()
    participant = Participant(session_id=fake_session_id, display_name="Hayalet")
    db_session.add(participant)
    with pytest.raises(IntegrityError):
        db_session.flush()


@requires_db
def test_reality_score_above_one_is_rejected(db_session) -> None:
    session_row = SessionModel(title="Demo")
    participant = Participant(session=session_row, display_name="Ayşe")
    model_version = ModelVersion(name="analysis-v1")
    db_session.add_all([session_row, participant, model_version])
    db_session.flush()

    bad_result = AnalysisResult(
        session_id=session_row.id,
        participant_id=participant.id,
        model_version_id=model_version.id,
        reality_score=1.5,
        confidence=0.5,
        status=ParticipantStatus.SUSPICIOUS,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(bad_result)
    with pytest.raises(IntegrityError):
        db_session.flush()


@requires_db
def test_confidence_below_zero_is_rejected(db_session) -> None:
    session_row = SessionModel(title="Demo")
    participant = Participant(session=session_row, display_name="Ayşe")
    model_version = ModelVersion(name="analysis-v1")
    db_session.add_all([session_row, participant, model_version])
    db_session.flush()

    bad_result = AnalysisResult(
        session_id=session_row.id,
        participant_id=participant.id,
        model_version_id=model_version.id,
        reality_score=0.5,
        confidence=-0.1,
        status=ParticipantStatus.SUSPICIOUS,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(bad_result)
    with pytest.raises(IntegrityError):
        db_session.flush()


@requires_db
def test_duplicate_face_sample_is_rejected(db_session) -> None:
    """Aynı video + aynı kare + aynı yüz sırası ikinci kez eklenemez."""
    method = ManipulationMethod(name="Deepfakes-test-constraint")
    db_session.add(method)
    db_session.flush()

    video = DatasetVideo(source_video_id="test_video_constraint", method_id=method.id)
    db_session.add(video)
    db_session.flush()

    sample1 = FaceSample(dataset_video_id=video.id, frame_reference=5, face_order=0)
    db_session.add(sample1)
    db_session.flush()

    sample2 = FaceSample(dataset_video_id=video.id, frame_reference=5, face_order=0)
    db_session.add(sample2)
    with pytest.raises(IntegrityError):
        db_session.flush()
