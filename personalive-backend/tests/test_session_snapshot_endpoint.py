from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db_session
from app.main import app
from app.models.analysis_result import AnalysisResult as AnalysisResultModel
from app.models.enums import ParticipantStatus
from app.models.model_version import ModelVersion
from app.models.participant import Participant
from app.models.session import Session as SessionModel
from tests.conftest import requires_db


pytestmark = requires_db


@pytest.fixture()
def client(db_session: DBSession) -> Iterator[TestClient]:
    def override_db_session() -> Iterator[DBSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.fixture()
def session(db_session: DBSession) -> SessionModel:
    session_row = SessionModel(title="Weekly Review")
    db_session.add(session_row)
    db_session.flush()
    return session_row


def add_participant(
    db_session: DBSession,
    session_row: SessionModel,
    *,
    display_name: str,
    joined_at: datetime | None = None,
    status: ParticipantStatus = ParticipantStatus.ANALYZING,
    left_at: datetime | None = None,
) -> Participant:
    participant = Participant(
        session=session_row,
        display_name=display_name,
        status=status,
        left_at=left_at,
    )
    if joined_at is not None:
        participant.joined_at = joined_at
    db_session.add(participant)
    db_session.flush()
    return participant


def add_analysis(
    db_session: DBSession,
    *,
    session_row: SessionModel,
    participant: Participant,
    timestamp: datetime,
    reality_score: float = 0.9,
    confidence: float = 0.85,
    status: ParticipantStatus = ParticipantStatus.AUTHENTIC,
    model_version_name: str = "analysis-v1",
) -> AnalysisResultModel:
    model_version = db_session.execute(
        select(ModelVersion).where(ModelVersion.name == model_version_name)
    ).scalar_one_or_none()
    if model_version is None:
        model_version = ModelVersion(name=model_version_name)
        db_session.add(model_version)
        db_session.flush()

    result = AnalysisResultModel(
        session_id=session_row.id,
        participant_id=participant.id,
        model_version=model_version,
        reality_score=reality_score,
        confidence=confidence,
        status=status,
        timestamp=timestamp,
    )
    db_session.add(result)
    db_session.flush()
    return result


# --- 1. unknown session -----------------------------------------------


def test_snapshot_unknown_session_returns_http_404(client: TestClient) -> None:
    response = client.get(f"/api/v1/sessions/{uuid4()}/snapshot")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


# --- 2. empty session ----------------------------------------------------


def test_snapshot_empty_session_returns_empty_participant_list(
    client: TestClient, session: SessionModel
) -> None:
    response = client.get(f"/api/v1/sessions/{session.id}/snapshot")

    assert response.status_code == 200
    body = response.json()
    assert body["session"]["sessionId"] == str(session.id)
    assert body["participants"] == []


# --- 3. participant with no analysis -------------------------------------


def test_snapshot_participant_without_analysis_has_null_latest_analysis(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    add_participant(db_session, session, display_name="Ayşe")
    db_session.commit()

    response = client.get(f"/api/v1/sessions/{session.id}/snapshot")

    assert response.status_code == 200
    body = response.json()
    assert len(body["participants"]) == 1
    assert body["participants"][0]["latestAnalysis"] is None


# --- 4. multiple analyses -> newest wins ----------------------------------


def test_snapshot_selects_newest_analysis_when_multiple_exist(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    participant = add_participant(db_session, session, display_name="Ayşe")
    older = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    newer = datetime(2026, 1, 15, 12, 5, tzinfo=timezone.utc)
    add_analysis(
        db_session,
        session_row=session,
        participant=participant,
        timestamp=older,
        reality_score=0.4,
        status=ParticipantStatus.SUSPICIOUS,
    )
    add_analysis(
        db_session,
        session_row=session,
        participant=participant,
        timestamp=newer,
        reality_score=0.9,
        status=ParticipantStatus.AUTHENTIC,
    )
    db_session.commit()

    response = client.get(f"/api/v1/sessions/{session.id}/snapshot")

    assert response.status_code == 200
    latest_analysis = response.json()["participants"][0]["latestAnalysis"]
    assert latest_analysis is not None
    # DB'den geri okunan zaman damgası, sunucunun oturum saat dilimi
    # ayarına göre farklı bir offset ile (örn. +03:00) dönebilir; metin
    # olarak değil, ifade ettiği ana göre karşılaştırıyoruz.
    returned_timestamp = datetime.fromisoformat(
        latest_analysis["timestamp"].replace("Z", "+00:00")
    )
    assert returned_timestamp == newer
    assert latest_analysis["realityScore"] == pytest.approx(0.9)
    assert latest_analysis["status"] == "authentic"


# --- 5. disconnected participant preserved --------------------------------


def test_snapshot_keeps_disconnected_participant_in_list(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    left_at = datetime(2026, 1, 15, 12, 10, tzinfo=timezone.utc)
    add_participant(
        db_session,
        session,
        display_name="Ayşe",
        status=ParticipantStatus.DISCONNECTED,
        left_at=left_at,
    )
    db_session.commit()

    response = client.get(f"/api/v1/sessions/{session.id}/snapshot")

    assert response.status_code == 200
    participants = response.json()["participants"]
    assert len(participants) == 1
    assert participants[0]["participant"]["status"] == "disconnected"
    assert participants[0]["participant"]["leftAt"] is not None


# --- 6. session isolation --------------------------------------------------


def test_snapshot_does_not_leak_other_sessions_data(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    own_participant = add_participant(db_session, session, display_name="Ayşe")
    add_analysis(
        db_session,
        session_row=session,
        participant=own_participant,
        timestamp=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
    )

    other_session = SessionModel(title="Other session")
    db_session.add(other_session)
    db_session.flush()
    other_participant = add_participant(
        db_session, other_session, display_name="Other"
    )
    add_analysis(
        db_session,
        session_row=other_session,
        participant=other_participant,
        timestamp=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
    )
    db_session.commit()

    response = client.get(f"/api/v1/sessions/{session.id}/snapshot")

    assert response.status_code == 200
    body = response.json()
    participant_ids = {p["participant"]["participantId"] for p in body["participants"]}
    assert str(own_participant.id) in participant_ids
    assert str(other_participant.id) not in participant_ids
    for participant_entry in body["participants"]:
        if participant_entry["latestAnalysis"] is not None:
            assert participant_entry["latestAnalysis"]["sessionId"] == str(session.id)


# --- 7. participant ordering: joinedAt ASC --------------------------------


def test_snapshot_orders_participants_by_joined_at_ascending(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    base = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    third = add_participant(
        db_session, session, display_name="Üçüncü", joined_at=base + timedelta(minutes=2)
    )
    first = add_participant(
        db_session, session, display_name="Birinci", joined_at=base
    )
    second = add_participant(
        db_session, session, display_name="İkinci", joined_at=base + timedelta(minutes=1)
    )
    db_session.commit()

    response = client.get(f"/api/v1/sessions/{session.id}/snapshot")

    assert response.status_code == 200
    ordered_ids = [
        p["participant"]["participantId"]
        for p in response.json()["participants"]
    ]
    assert ordered_ids == [str(first.id), str(second.id), str(third.id)]


# --- 8. response contract validation ---------------------------------------


def test_snapshot_response_matches_expected_contract_shape(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    participant = add_participant(db_session, session, display_name="Ayşe")
    add_analysis(
        db_session,
        session_row=session,
        participant=participant,
        timestamp=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
    )
    db_session.commit()

    response = client.get(f"/api/v1/sessions/{session.id}/snapshot")

    assert response.status_code == 200
    body = response.json()

    assert set(body.keys()) == {"session", "participants"}
    session_fields = body["session"]
    assert set(session_fields.keys()) == {
        "sessionId",
        "title",
        "status",
        "createdAt",
        "startedAt",
        "endedAt",
    }

    entry = body["participants"][0]
    assert set(entry.keys()) == {"participant", "latestAnalysis"}
    assert set(entry["participant"].keys()) == {
        "participantId",
        "sessionId",
        "displayName",
        "status",
        "joinedAt",
        "leftAt",
    }
    assert set(entry["latestAnalysis"].keys()) == {
        "sessionId",
        "participantId",
        "realityScore",
        "confidence",
        "status",
        "timestamp",
        "modelVersion",
    }


def test_snapshot_invalid_session_uuid_returns_http_422(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/not-a-uuid/snapshot")

    assert response.status_code == 422
