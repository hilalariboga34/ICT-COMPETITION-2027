import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

SESSION_ID = "11111111-1111-4111-8111-111111111111"
PARTICIPANT_ID = "22222222-2222-4222-8222-222222222222"
UTC_TIMESTAMP = "2026-01-15T12:30:00Z"


def valid_request_body() -> dict[str, object]:
    return {
        "sessionId": SESSION_ID,
        "participantId": PARTICIPANT_ID,
        "fakeProbability": 0.25,
        "confidence": 0.9,
        "timestamp": UTC_TIMESTAMP,
        "modelVersion": "analysis-v1",
    }


def test_evaluate_returns_http_200_for_valid_body() -> None:
    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    assert response.status_code == 200


def test_evaluate_returns_expected_reality_score() -> None:
    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    assert response.json()["realityScore"] == pytest.approx(0.75)


def test_evaluate_returns_authentic_status() -> None:
    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())

    assert response.json()["status"] == "authentic"


def test_evaluate_preserves_common_fields() -> None:
    response = client.post("/api/v1/analysis/evaluate", json=valid_request_body())
    response_body = response.json()

    assert response_body["sessionId"] == SESSION_ID
    assert response_body["participantId"] == PARTICIPANT_ID
    assert response_body["confidence"] == pytest.approx(0.9)
    assert response_body["timestamp"] == UTC_TIMESTAMP
    assert response_body["modelVersion"] == "analysis-v1"


def test_evaluate_rejects_fake_probability_above_one() -> None:
    request_body = valid_request_body()
    request_body["fakeProbability"] = 1.01

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 422


def test_evaluate_rejects_timestamp_without_timezone() -> None:
    request_body = valid_request_body()
    request_body["timestamp"] = "2026-01-15T12:30:00"

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 422


def test_evaluate_rejects_extra_field() -> None:
    request_body = valid_request_body()
    request_body["unexpectedField"] = "unexpected"

    response = client.post("/api/v1/analysis/evaluate", json=request_body)

    assert response.status_code == 422
