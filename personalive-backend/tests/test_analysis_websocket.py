from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db_session
from app.main import app
from app.models.participant import Participant
from app.models.session import Session as SessionModel
from tests.conftest import requires_db


pytestmark = requires_db

SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
PARTICIPANT_ID = UUID("22222222-2222-4222-8222-222222222222")
UTC_TIMESTAMP = "2026-01-15T12:30:00Z"
WEBSOCKET_PATH = f"/api/v1/ws/sessions/{SESSION_ID}"
EVALUATE_PATH = "/api/v1/analysis/evaluate"


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
def session_and_participant(db_session: DBSession) -> None:
    session = SessionModel(id=SESSION_ID, title="WebSocket test")
    participant = Participant(
        id=PARTICIPANT_ID,
        session=session,
        display_name="Ayse",
    )
    db_session.add_all([session, participant])
    db_session.commit()


def valid_request_body() -> dict[str, object]:
    return {
        "sessionId": str(SESSION_ID),
        "participantId": str(PARTICIPANT_ID),
        "fakeProbability": 0.25,
        "confidence": 0.9,
        "timestamp": UTC_TIMESTAMP,
        "modelVersion": "analysis-v1",
    }


def test_session_websocket_connection_can_open(client: TestClient) -> None:
    with client.websocket_connect(WEBSOCKET_PATH) as websocket:
        assert websocket is not None


def test_evaluate_returns_http_200_with_connected_websocket(
    client: TestClient,
    session_and_participant: None,
) -> None:
    with client.websocket_connect(WEBSOCKET_PATH):
        response = client.post(EVALUATE_PATH, json=valid_request_body())

    assert response.status_code == 200


def test_websocket_event_has_analysis_updated_type(
    client: TestClient,
    session_and_participant: None,
) -> None:
    with client.websocket_connect(WEBSOCKET_PATH) as websocket:
        response = client.post(EVALUATE_PATH, json=valid_request_body())
        response.raise_for_status()
        event = websocket.receive_json()

    assert event["type"] == "analysis.updated"


def test_websocket_event_preserves_session_and_participant_ids(
    client: TestClient,
    session_and_participant: None,
) -> None:
    with client.websocket_connect(WEBSOCKET_PATH) as websocket:
        response = client.post(EVALUATE_PATH, json=valid_request_body())
        response.raise_for_status()
        event = websocket.receive_json()

    assert event["data"]["sessionId"] == str(SESSION_ID)
    assert event["data"]["participantId"] == str(PARTICIPANT_ID)


def test_websocket_event_contains_expected_analysis(
    client: TestClient,
    session_and_participant: None,
) -> None:
    with client.websocket_connect(WEBSOCKET_PATH) as websocket:
        response = client.post(EVALUATE_PATH, json=valid_request_body())
        response.raise_for_status()
        event = websocket.receive_json()

    assert event["data"]["realityScore"] == pytest.approx(0.75)
    assert event["data"]["status"] == "authentic"


def test_evaluate_returns_http_200_without_websocket_connection(
    client: TestClient,
    session_and_participant: None,
) -> None:
    response = client.post(EVALUATE_PATH, json=valid_request_body())

    assert response.status_code == 200
