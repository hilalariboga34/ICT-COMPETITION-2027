import argparse
import random
from datetime import datetime, timezone
from uuid import UUID

import httpx
import pytest

from app.schemas.analysis import AnalysisInput
from scripts.mock_analysis_publisher import (
    PublisherError,
    build_analysis_payload,
    generate_participant_ids,
    positive_int,
    post_analysis,
)


SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
FIXED_TIMESTAMP = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)


def test_generated_request_matches_analysis_input_contract() -> None:
    participant_id = generate_participant_ids(SESSION_ID, 1)[0]
    payload = build_analysis_payload(
        session_id=SESSION_ID,
        participant_id=participant_id,
        model_version="mock-model-v1",
        rng=random.Random(42),
        timestamp=FIXED_TIMESTAMP,
    )

    analysis_input = AnalysisInput.model_validate(payload)

    assert analysis_input.sessionId == SESSION_ID
    assert analysis_input.participantId == participant_id
    assert analysis_input.modelVersion == "mock-model-v1"


def test_same_session_and_seed_produce_deterministic_values() -> None:
    first_participants = generate_participant_ids(SESSION_ID, 3)
    second_participants = generate_participant_ids(SESSION_ID, 3)
    first_rng = random.Random(42)
    second_rng = random.Random(42)

    first_payloads = [
        build_analysis_payload(
            SESSION_ID,
            participant_id,
            "mock-model-v1",
            first_rng,
            FIXED_TIMESTAMP,
        )
        for participant_id in first_participants
    ]
    second_payloads = [
        build_analysis_payload(
            SESSION_ID,
            participant_id,
            "mock-model-v1",
            second_rng,
            FIXED_TIMESTAMP,
        )
        for participant_id in second_participants
    ]

    assert first_participants == second_participants
    assert first_payloads == second_payloads


@pytest.mark.parametrize("participant_count", ["0", "-1"])
def test_non_positive_participant_count_is_rejected(
    participant_count: str,
) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int(participant_count)


def test_generated_probabilities_are_between_zero_and_one() -> None:
    participant_id = generate_participant_ids(SESSION_ID, 1)[0]
    rng = random.Random(42)

    for _ in range(100):
        payload = build_analysis_payload(
            SESSION_ID,
            participant_id,
            "mock-model-v1",
            rng,
            FIXED_TIMESTAMP,
        )

        assert 0.0 <= payload["fakeProbability"] <= 1.0
        assert 0.0 <= payload["confidence"] <= 1.0


def test_successful_http_response_is_processed() -> None:
    expected_response = {
        "participantId": "22222222-2222-4222-8222-222222222222",
        "realityScore": 0.75,
        "status": "authentic",
    }
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=expected_response)
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        response_data = post_analysis(client, {"example": "payload"})

    assert response_data == expected_response


def test_http_error_response_raises_publisher_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(422, json={"detail": "invalid payload"})
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError, match="HTTP 422"):
            post_analysis(client, {"example": "payload"})
