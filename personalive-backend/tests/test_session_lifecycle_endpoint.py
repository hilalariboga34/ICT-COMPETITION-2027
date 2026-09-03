from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db_session
from app.main import app
from app.models.participant import Participant
from app.models.session import Session as SessionModel
from app.repositories.session import SessionRepository
from app.services.sessions import SessionService
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


# --- start ------------------------------------------------------------


def test_start_waiting_session_returns_http_200(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(f"/api/v1/sessions/{session.id}/start")

    assert response.status_code == 200


def test_start_waiting_session_sets_status_and_started_at(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(f"/api/v1/sessions/{session.id}/start")
    body = response.json()

    assert body["status"] == "active"
    assert body["startedAt"] is not None
    assert body["endedAt"] is None


def test_start_already_active_session_returns_http_409(
    client: TestClient, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")

    response = client.post(f"/api/v1/sessions/{session.id}/start")

    assert response.status_code == 409


def test_start_ended_session_returns_http_409(
    client: TestClient, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")
    client.post(f"/api/v1/sessions/{session.id}/end")

    response = client.post(f"/api/v1/sessions/{session.id}/start")

    assert response.status_code == 409


def test_start_unknown_session_returns_http_404(client: TestClient) -> None:
    response = client.post(f"/api/v1/sessions/{uuid4()}/start")

    assert response.status_code == 404


def test_start_invalid_session_uuid_returns_http_422(client: TestClient) -> None:
    response = client.post("/api/v1/sessions/not-a-uuid/start")

    assert response.status_code == 422


# --- end ----------------------------------------------------------------


def test_end_active_session_returns_http_200(
    client: TestClient, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")

    response = client.post(f"/api/v1/sessions/{session.id}/end")

    assert response.status_code == 200


def test_end_active_session_sets_status_and_ended_at(
    client: TestClient, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")

    response = client.post(f"/api/v1/sessions/{session.id}/end")
    body = response.json()

    assert body["status"] == "ended"
    assert body["endedAt"] is not None


def test_end_waiting_session_returns_http_409(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(f"/api/v1/sessions/{session.id}/end")

    assert response.status_code == 409


def test_end_already_ended_session_returns_http_409(
    client: TestClient, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")
    client.post(f"/api/v1/sessions/{session.id}/end")

    response = client.post(f"/api/v1/sessions/{session.id}/end")

    assert response.status_code == 409


def test_end_unknown_session_returns_http_404(client: TestClient) -> None:
    response = client.post(f"/api/v1/sessions/{uuid4()}/end")

    assert response.status_code == 404


def test_end_invalid_session_uuid_returns_http_422(client: TestClient) -> None:
    response = client.post("/api/v1/sessions/not-a-uuid/end")

    assert response.status_code == 422


def test_end_session_disconnects_active_participants(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")
    create_response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = create_response.json()["participantId"]

    client.post(f"/api/v1/sessions/{session.id}/end")

    persisted = db_session.get(Participant, participant_id)
    assert persisted is not None
    assert persisted.status.value == "disconnected"
    assert persisted.left_at is not None


def test_end_session_does_not_touch_already_disconnected_participant(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")
    create_response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = create_response.json()["participantId"]
    client.post(
        f"/api/v1/sessions/{session.id}/participants/{participant_id}/disconnect"
    )
    left_at_before_end = db_session.get(Participant, participant_id).left_at

    client.post(f"/api/v1/sessions/{session.id}/end")

    persisted = db_session.get(Participant, participant_id)
    assert persisted is not None
    assert persisted.left_at == left_at_before_end


def test_end_session_does_not_delete_participant_row(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")
    create_response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = create_response.json()["participantId"]

    client.post(f"/api/v1/sessions/{session.id}/end")

    persisted = db_session.get(Participant, participant_id)
    assert persisted is not None
    assert persisted.display_name == "Ayşe"


def test_end_session_does_not_break_get_session_endpoint(
    client: TestClient, session: SessionModel
) -> None:
    client.post(f"/api/v1/sessions/{session.id}/start")
    client.post(f"/api/v1/sessions/{session.id}/end")

    response = client.get(f"/api/v1/sessions/{session.id}")

    assert response.status_code == 200
    assert response.json()["status"] == "ended"


# --- concurrency: start/end must request a row lock -----------------------


def test_start_requests_row_lock(
    db_session: DBSession, session: SessionModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_get_by_id = SessionRepository.get_by_id
    calls: list[bool] = []

    def spy_get_by_id(
        self: SessionRepository, session_id, *, for_update: bool = False
    ):
        calls.append(for_update)
        return original_get_by_id(self, session_id, for_update=for_update)

    monkeypatch.setattr(SessionRepository, "get_by_id", spy_get_by_id)

    SessionService(db_session).start(session.id)

    assert calls == [True]


def test_end_requests_row_lock(
    db_session: DBSession, session: SessionModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    SessionService(db_session).start(session.id)

    original_get_by_id = SessionRepository.get_by_id
    calls: list[bool] = []

    def spy_get_by_id(
        self: SessionRepository, session_id, *, for_update: bool = False
    ):
        calls.append(for_update)
        return original_get_by_id(self, session_id, for_update=for_update)

    monkeypatch.setattr(SessionRepository, "get_by_id", spy_get_by_id)

    SessionService(db_session).end(session.id)

    assert calls == [True]


def test_get_session_service_does_not_request_row_lock(
    db_session: DBSession, session: SessionModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_get_by_id = SessionRepository.get_by_id
    calls: list[bool] = []

    def spy_get_by_id(
        self: SessionRepository, session_id, *, for_update: bool = False
    ):
        calls.append(for_update)
        return original_get_by_id(self, session_id, for_update=for_update)

    monkeypatch.setattr(SessionRepository, "get_by_id", spy_get_by_id)

    SessionService(db_session).get_by_id(session.id)

    assert calls == [False]
