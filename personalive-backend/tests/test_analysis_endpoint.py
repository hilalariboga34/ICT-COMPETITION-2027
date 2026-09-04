from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.api.routes import analysis as analysis_route
from app.db.session import get_db_session
from app.main import app
from app.models.analysis_result import AnalysisResult as AnalysisResultModel
from app.models.enums import ParticipantStatus
from app.models.model_version import ModelVersion
from app.models.participant import Participant
from app.models.session import Session as SessionModel
from tests.conftest import requires_db


pytestmark = requires_db

SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
PARTICIPANT_ID = UUID("22222222-2222-4222-8222-222222222222")
UTC_TIMESTAMP = "2026-01-15T12:30:00Z"


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
def session_and_participant(
    db_session: DBSession,
) -> tuple[SessionModel, Participant]:
    session = SessionModel(id=SESSION_ID, title="Analysis test")
    participant = Participant(
        id=PARTICIPANT_ID,
        session=session,
        display_name="Ayse",
    )
    db_session.add_all([session, participant])
    db_session.commit()
    return session, participant


def valid_request_body() -> dict[str, object]:
    return {
        "sessionId": str(SESSION_ID),
        "participantId": str(PARTICIPANT_ID),
        "fakeProbability": 0.25,
        "confidence": 0.9,
        "timestamp": UTC_TIMESTAMP,
        "modelVersion": "analysis-v1",
    }


def persisted_results(db_session: DBSession) -> list[AnalysisResultModel]:
    statement = select(AnalysisResultModel).where(
        AnalysisResultModel.session_id == SESSION_ID,
        AnalysisResultModel.participant_id == PARTICIPANT_ID,
    )
    return list(db_session.execute(statement).scalars().all())


def test_evaluate_returns_http_200_for_valid_body(
    client: TestClient,
    session_and_participant: tuple[SessionModel, Participant],
) -> None:
    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    assert response.status_code == 200


def test_evaluate_returns_http_422_when_model_version_exceeds_64_characters(
    client: TestClient,
) -> None:
    body = valid_request_body()
    body["modelVersion"] = "a" * 65

    response = client.post("/api/v1/analysis/evaluate", json=body)

    assert response.status_code == 422


def test_evaluate_returns_expected_result_fields(
    client: TestClient,
    session_and_participant: tuple[SessionModel, Participant],
) -> None:
    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())
    body = response.json()

    assert body["sessionId"] == str(SESSION_ID)
    assert body["participantId"] == str(PARTICIPANT_ID)
    assert body["realityScore"] == pytest.approx(0.75)
    assert body["confidence"] == pytest.approx(0.9)
    assert body["status"] == "authentic"
    assert body["timestamp"] == UTC_TIMESTAMP
    assert body["modelVersion"] == "analysis-v1"


def test_evaluate_uses_configured_authentic_threshold(
    client: TestClient,
    session_and_participant: tuple[SessionModel, Participant],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(analysis_route.settings, "authentic_threshold", 0.80)

    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    assert response.status_code == 200
    assert response.json()["realityScore"] == pytest.approx(0.75)
    assert response.json()["status"] == "suspicious"


def test_evaluate_persists_all_analysis_fields_and_model_version(
    client: TestClient,
    db_session: DBSession,
    session_and_participant: tuple[SessionModel, Participant],
) -> None:
    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())
    response.raise_for_status()

    persisted = persisted_results(db_session)
    assert len(persisted) == 1
    result = persisted[0]
    model_version = db_session.get(ModelVersion, result.model_version_id)

    assert result.session_id == SESSION_ID
    assert result.participant_id == PARTICIPANT_ID
    assert result.reality_score == pytest.approx(0.75)
    assert result.confidence == pytest.approx(0.9)
    assert result.status == ParticipantStatus.AUTHENTIC
    assert result.timestamp == datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)
    assert model_version is not None
    assert model_version.name == "analysis-v1"


@pytest.mark.parametrize(
    ("fake_probability", "expected_status"),
    [(0.25, ParticipantStatus.AUTHENTIC), (0.75, ParticipantStatus.SUSPICIOUS)],
)
def test_evaluate_updates_participant_status_without_changing_left_at(
    client: TestClient,
    db_session: DBSession,
    session_and_participant: tuple[SessionModel, Participant],
    fake_probability: float,
    expected_status: ParticipantStatus,
) -> None:
    _, participant = session_and_participant
    original_left_at = participant.left_at
    request_body = valid_request_body()
    request_body["fakeProbability"] = fake_probability

    response = client.post("/api/v1/analysis/evaluate", json=request_body)
    response.raise_for_status()
    db_session.refresh(participant)

    assert participant.status == expected_status
    assert participant.left_at == original_left_at


def test_evaluate_reuses_existing_model_version_without_duplicate(
    client: TestClient,
    db_session: DBSession,
    session_and_participant: tuple[SessionModel, Participant],
) -> None:
    first_response = client.post(
        "/api/v1/analysis/evaluate", json=valid_request_body()
    )
    second_body = valid_request_body()
    second_body["timestamp"] = "2026-01-15T12:30:01Z"
    second_response = client.post("/api/v1/analysis/evaluate", json=second_body)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    model_versions = list(
        db_session.execute(
            select(ModelVersion).where(ModelVersion.name == "analysis-v1")
        )
        .scalars()
        .all()
    )
    results = persisted_results(db_session)
    assert len(model_versions) == 1
    assert len(results) == 2
    assert {result.model_version_id for result in results} == {
        model_versions[0].id
    }


def test_evaluate_unknown_session_returns_http_404(
    client: TestClient,
    session_and_participant: tuple[SessionModel, Participant],
) -> None:
    request_body = valid_request_body()
    request_body["sessionId"] = str(uuid4())

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


def test_evaluate_unknown_participant_returns_http_404(
    client: TestClient,
    session_and_participant: tuple[SessionModel, Participant],
) -> None:
    request_body = valid_request_body()
    request_body["participantId"] = str(uuid4())

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_evaluate_participant_from_other_session_returns_http_404(
    client: TestClient,
    db_session: DBSession,
    session_and_participant: tuple[SessionModel, Participant],
) -> None:
    other_session = SessionModel(title="Other session")
    other_participant = Participant(session=other_session, display_name="Other")
    db_session.add_all([other_session, other_participant])
    db_session.commit()
    request_body = valid_request_body()
    request_body["participantId"] = str(other_participant.id)

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_evaluate_disconnected_participant_returns_409_and_changes_nothing(
    client: TestClient,
    db_session: DBSession,
    session_and_participant: tuple[SessionModel, Participant],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, participant = session_and_participant
    left_at = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    participant.status = ParticipantStatus.DISCONNECTED
    participant.left_at = left_at
    db_session.commit()
    broadcast = AsyncMock()
    monkeypatch.setattr(
        analysis_route.connection_manager, "broadcast_analysis", broadcast
    )

    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    assert response.status_code == 409
    assert persisted_results(db_session) == []
    db_session.refresh(participant)
    assert participant.status == ParticipantStatus.DISCONNECTED
    assert participant.left_at == left_at
    broadcast.assert_not_awaited()


@pytest.mark.parametrize(
    "timestamp", ["2026-01-15T12:29:59Z", "2026-01-15T12:30:00Z"]
)
def test_evaluate_stale_or_duplicate_timestamp_returns_409_without_changes(
    client: TestClient,
    db_session: DBSession,
    session_and_participant: tuple[SessionModel, Participant],
    monkeypatch: pytest.MonkeyPatch,
    timestamp: str,
) -> None:
    _, participant = session_and_participant
    model_version = ModelVersion(name="existing-model")
    existing_result = AnalysisResultModel(
        session_id=SESSION_ID,
        participant_id=PARTICIPANT_ID,
        model_version=model_version,
        reality_score=0.4,
        confidence=0.8,
        status=ParticipantStatus.SUSPICIOUS,
        timestamp=datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc),
    )
    participant.status = ParticipantStatus.SUSPICIOUS
    db_session.add(existing_result)
    db_session.commit()
    model_version_count_before = db_session.execute(
        select(func.count()).select_from(ModelVersion)
    ).scalar_one()
    broadcast = AsyncMock()
    monkeypatch.setattr(
        analysis_route.connection_manager, "broadcast_analysis", broadcast
    )
    request_body = valid_request_body()
    request_body["timestamp"] = timestamp

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 409
    assert len(persisted_results(db_session)) == 1
    db_session.refresh(participant)
    assert participant.status == ParticipantStatus.SUSPICIOUS
    assert participant.left_at is None
    model_version_count_after = db_session.execute(
        select(func.count()).select_from(ModelVersion)
    ).scalar_one()
    assert model_version_count_after == model_version_count_before
    broadcast.assert_not_awaited()


def test_evaluate_newer_timestamp_is_accepted(
    client: TestClient,
    db_session: DBSession,
    session_and_participant: tuple[SessionModel, Participant],
) -> None:
    existing_model = ModelVersion(name="existing-model")
    db_session.add(
        AnalysisResultModel(
            session_id=SESSION_ID,
            participant_id=PARTICIPANT_ID,
            model_version=existing_model,
            reality_score=0.4,
            confidence=0.8,
            status=ParticipantStatus.SUSPICIOUS,
            timestamp=datetime(2026, 1, 15, 12, 29, 59, tzinfo=timezone.utc),
        )
    )
    db_session.commit()

    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    assert response.status_code == 200
    assert len(persisted_results(db_session)) == 2


def test_evaluate_broadcasts_once_after_successful_commit(
    client: TestClient,
    session_and_participant: tuple[SessionModel, Participant],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    broadcast = AsyncMock()
    monkeypatch.setattr(
        analysis_route.connection_manager, "broadcast_analysis", broadcast
    )

    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    assert response.status_code == 200
    broadcast.assert_awaited_once()
    event = broadcast.await_args.args[1]
    assert broadcast.await_args.args[0] == SESSION_ID
    assert event.type == "analysis.updated"
    assert event.data.model_dump(mode="json") == response.json()


def test_evaluate_commit_failure_rolls_back_and_does_not_broadcast(
    client: TestClient,
    db_session: DBSession,
    session_and_participant: tuple[SessionModel, Participant],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, participant = session_and_participant
    original_rollback = db_session.rollback
    rollback = Mock(wraps=original_rollback)
    broadcast = AsyncMock()
    monkeypatch.setattr(db_session, "rollback", rollback)
    monkeypatch.setattr(
        db_session, "commit", Mock(side_effect=RuntimeError("commit failed"))
    )
    monkeypatch.setattr(
        analysis_route.connection_manager, "broadcast_analysis", broadcast
    )

    with pytest.raises(RuntimeError, match="commit failed"):
        client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    rollback.assert_called_once_with()
    broadcast.assert_not_awaited()
    assert persisted_results(db_session) == []
    db_session.refresh(participant)
    assert participant.status == ParticipantStatus.ANALYZING


def test_evaluate_rejects_fake_probability_above_one(client: TestClient) -> None:
    request_body = valid_request_body()
    request_body["fakeProbability"] = 1.01

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 422


def test_evaluate_rejects_timestamp_without_timezone(client: TestClient) -> None:
    request_body = valid_request_body()
    request_body["timestamp"] = "2026-01-15T12:30:00"

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 422


def test_evaluate_rejects_extra_field(client: TestClient) -> None:
    request_body = valid_request_body()
    request_body["unexpectedField"] = "unexpected"

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 422
