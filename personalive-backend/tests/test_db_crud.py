"""Temel veritabanı akışları: bağlantı, session/participant/analysis
oluşturma. Gerçek local PostgreSQL gerektirir (bkz. conftest.requires_db)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from app.models import AnalysisResult, ModelVersion, Participant
from app.models import Session as SessionModel
from app.models.enums import ParticipantStatus, SessionStatus
from tests.conftest import requires_db


@requires_db
def test_connection_works(db_session) -> None:
    assert db_session.execute(text("SELECT 1")).scalar() == 1


@requires_db
def test_create_session(db_session) -> None:
    session_row = SessionModel(title="Demo Toplantı")
    db_session.add(session_row)
    db_session.flush()

    assert isinstance(session_row.id, uuid.UUID)
    assert session_row.status == SessionStatus.WAITING
    assert session_row.created_at is not None
    assert session_row.started_at is None
    assert session_row.ended_at is None


@requires_db
def test_add_participant(db_session) -> None:
    session_row = SessionModel(title="Demo Toplantı")
    db_session.add(session_row)
    db_session.flush()

    participant = Participant(session_id=session_row.id, display_name="Ayşe")
    db_session.add(participant)
    db_session.flush()

    assert participant.status == ParticipantStatus.ANALYZING
    assert participant.session_id == session_row.id
    assert participant.left_at is None


@requires_db
def test_add_analysis_result(db_session) -> None:
    session_row = SessionModel(title="Demo Toplantı")
    participant = Participant(session=session_row, display_name="Ayşe")
    model_version = ModelVersion(name="analysis-v1")
    db_session.add_all([session_row, participant, model_version])
    db_session.flush()

    result = AnalysisResult(
        session_id=session_row.id,
        participant_id=participant.id,
        model_version_id=model_version.id,
        reality_score=0.82,
        confidence=0.9,
        status=ParticipantStatus.AUTHENTIC,
        timestamp=datetime.now(timezone.utc),
    )
    db_session.add(result)
    db_session.flush()

    assert result.id is not None
    assert result.reality_score == pytest.approx(0.82)
    assert result.status == ParticipantStatus.AUTHENTIC


@requires_db
def test_participant_left_updates_status_not_delete(db_session) -> None:
    """Hilal'in kuralı: katılımcı ayrılınca kayıt silinmez, left_at +
    status='disconnected' güncellenir."""
    session_row = SessionModel(title="Demo Toplantı")
    participant = Participant(session=session_row, display_name="Ayşe")
    db_session.add_all([session_row, participant])
    db_session.flush()
    participant_id = participant.id

    participant.left_at = datetime.now(timezone.utc)
    participant.status = ParticipantStatus.DISCONNECTED
    db_session.flush()

    still_there = db_session.get(Participant, participant_id)
    assert still_there is not None
    assert still_there.left_at is not None
    assert still_there.status == ParticipantStatus.DISCONNECTED


@requires_db
def test_session_ended_updates_status_not_delete(db_session) -> None:
    """Hilal'in kuralı: session fiziksel silinmez, status='ended' olur."""
    session_row = SessionModel(title="Demo Toplantı")
    db_session.add(session_row)
    db_session.flush()
    session_id = session_row.id

    session_row.status = SessionStatus.ENDED
    session_row.ended_at = datetime.now(timezone.utc)
    db_session.flush()

    still_there = db_session.get(SessionModel, session_id)
    assert still_there is not None
    assert still_there.status == SessionStatus.ENDED
    assert still_there.ended_at is not None
