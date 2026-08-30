import pytest
from fastapi.testclient import TestClient

from app.main import app


SESSION_ID = "11111111-1111-4111-8111-111111111111"
PARTICIPANT_ID = "22222222-2222-4222-8222-222222222222"
UTC_TIMESTAMP = "2026-01-15T12:30:00Z"
WEBSOCKET_PATH = f"/api/v1/ws/sessions/{SESSION_ID}"
EVALUATE_PATH = "/api/v1/analysis/evaluate"


def valid_request_body() -> dict[str, object]:
    return {
        "sessionId": SESSION_ID,
        "participantId": PARTICIPANT_ID,
        "fakeProbability": 0.25,
        "confidence": 0.9,
        "timestamp": UTC_TIMESTAMP,
        "modelVersion": "analysis-v1",
    }


def test_session_websocket_connection_can_open() -> None:
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_PATH) as websocket:
            assert websocket is not None


def test_evaluate_returns_http_200_with_connected_websocket() -> None:
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_PATH):
            response = client.post(EVALUATE_PATH, json=valid_request_body())

    assert response.status_code == 200


def test_websocket_event_has_analysis_updated_type() -> None:
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_PATH) as websocket:
            response = client.post(EVALUATE_PATH, json=valid_request_body())
            response.raise_for_status()
            event = websocket.receive_json()

    assert event["type"] == "analysis.updated"


def test_websocket_event_preserves_session_and_participant_ids() -> None:
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_PATH) as websocket:
            response = client.post(EVALUATE_PATH, json=valid_request_body())
            response.raise_for_status()
            event = websocket.receive_json()

    assert event["data"]["sessionId"] == SESSION_ID
    assert event["data"]["participantId"] == PARTICIPANT_ID


def test_websocket_event_contains_expected_analysis() -> None:
    with TestClient(app) as client:
        with client.websocket_connect(WEBSOCKET_PATH) as websocket:
            response = client.post(EVALUATE_PATH, json=valid_request_body())
            response.raise_for_status()
            event = websocket.receive_json()

    assert event["data"]["realityScore"] == pytest.approx(0.75)
    assert event["data"]["status"] == "authentic"


def test_evaluate_returns_http_200_without_websocket_connection() -> None:
    with TestClient(app) as client:
        response = client.post(EVALUATE_PATH, json=valid_request_body())

    assert response.status_code == 200
