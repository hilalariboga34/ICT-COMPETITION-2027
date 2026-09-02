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
def test_analysis_result_with_participant_from_other_session_is_rejected(
    db_session,
) -> None:
    """Hilal'in kuralı: Session A'ya, Session B'deki bir participant ile
    analiz kaydı eklenememeli — bu composite foreign key (participant_id,
    session_id) -> participants(id, session_id) ile DB seviyesinde
    doğrulanıyor (bkz. app/models/analysis_result.py)."""
    session_a = SessionModel(title="Session A")
    session_b = SessionModel(title="Session B")
    participant_in_b = Participant(session=session_b, display_name="Fatma")
    model_version = ModelVersion(name="test-model-v1")
    db_session.add_all([session_a, session_b, participant_in_b, model_version])
    db_session.flush()

    mismatched_result = AnalysisResult(
        session_id=session_a.id,  # Session A
        participant_id=participant_in_b.id,  # ama participant Session B'de
        model_version_id=model_version.id,
        reality_score=0.5,
        confidence=0.5,
        status=ParticipantStatus.SUSPICIOUS,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(mismatched_result)
    with pytest.raises(IntegrityError):
        db_session.flush()


@requires_db
def test_dataset_video_label_must_be_binary(db_session) -> None:
    method = ManipulationMethod(name="Deepfakes-test-label")
    db_session.add(method)
    db_session.flush()

    video = DatasetVideo(source_video_id="bad_label_video", method_id=method.id, label=2)
    db_session.add(video)
    with pytest.raises(IntegrityError):
        db_session.flush()


@requires_db
def test_face_sample_label_must_be_binary(db_session) -> None:
    method = ManipulationMethod(name="Deepfakes-test-face-label")
    db_session.add(method)
    db_session.flush()
    video = DatasetVideo(source_video_id="face_label_video", method_id=method.id)
    db_session.add(video)
    db_session.flush()

    sample = FaceSample(dataset_video_id=video.id, frame_reference=0, face_order=0, label=5)
    db_session.add(sample)
    with pytest.raises(IntegrityError):
        db_session.flush()


@requires_db
def test_face_sample_frame_reference_cannot_be_negative(db_session) -> None:
    method = ManipulationMethod(name="Deepfakes-test-frame-ref")
    db_session.add(method)
    db_session.flush()
    video = DatasetVideo(source_video_id="negative_frame_video", method_id=method.id)
    db_session.add(video)
    db_session.flush()

    sample = FaceSample(dataset_video_id=video.id, frame_reference=-1, face_order=0)
    db_session.add(sample)
    with pytest.raises(IntegrityError):
        db_session.flush()


@requires_db
def test_face_sample_face_order_cannot_be_negative(db_session) -> None:
    method = ManipulationMethod(name="Deepfakes-test-face-order")
    db_session.add(method)
    db_session.flush()
    video = DatasetVideo(source_video_id="negative_order_video", method_id=method.id)
    db_session.add(video)
    db_session.flush()

    sample = FaceSample(dataset_video_id=video.id, frame_reference=0, face_order=-1)
    db_session.add(sample)
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
