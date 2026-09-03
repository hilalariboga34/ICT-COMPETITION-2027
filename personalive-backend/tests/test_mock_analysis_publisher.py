from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from uuid import UUID

import httpx
import pytest

from app.schemas.analysis import AnalysisInput
from scripts import mock_analysis_publisher as publisher
from scripts.mock_analysis_publisher import (
    PublisherError,
    build_analysis_payload,
    create_session,
    list_active_participants,
    next_analysis_timestamp,
    non_negative_float,
    positive_int,
    post_analysis,
    prepare_participant_ids,
    prepare_session,
)


SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
PARTICIPANT_ID_1 = UUID("22222222-2222-4222-8222-222222222222")
PARTICIPANT_ID_2 = UUID("33333333-3333-4333-8333-333333333333")
PARTICIPANT_ID_3 = UUID("44444444-4444-4444-8444-444444444444")
DISCONNECTED_ID = UUID("55555555-5555-4555-8555-555555555555")
FIXED_TIMESTAMP = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)


def session_response(session_id: UUID = SESSION_ID) -> dict[str, object]:
    return {
        "sessionId": str(session_id),
        "title": "Mock Analysis Session",
        "status": "waiting",
        "createdAt": "2026-01-15T12:00:00Z",
        "startedAt": None,
        "endedAt": None,
    }


def participant_response(
    participant_id: UUID,
    *,
    status: str = "analyzing",
    display_name: str = "Mock Participant",
) -> dict[str, object]:
    return {
        "participantId": str(participant_id),
        "sessionId": str(SESSION_ID),
        "displayName": display_name,
        "status": status,
        "joinedAt": "2026-01-15T12:05:00Z",
        "leftAt": "2026-01-15T12:10:00Z" if status == "disconnected" else None,
    }


def analysis_response(payload: dict[str, object]) -> dict[str, object]:
    return {
        "sessionId": payload["sessionId"],
        "participantId": payload["participantId"],
        "realityScore": 1.0 - float(payload["fakeProbability"]),
        "confidence": payload["confidence"],
        "status": "authentic",
        "timestamp": payload["timestamp"],
        "modelVersion": payload["modelVersion"],
    }


def request_json(request: httpx.Request) -> dict[str, object]:
    return json.loads(request.content)


def test_parser_defaults_to_creating_a_session_with_readable_title() -> None:
    args = publisher.build_parser().parse_args([])

    assert args.session_id is None
    assert args.session_title == "Mock Analysis Session"


def test_help_describes_session_and_participant_options() -> None:
    help_text = publisher.build_parser().format_help()

    assert "--session-id" in help_text
    assert "--session-title" in help_text
    assert "--participant-count" in help_text
    assert "yeni session" in help_text.lower()


def test_prepare_session_creates_session_when_id_is_not_given() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(201, json=session_response())

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        session_id = prepare_session(client, None, "Demo Session")

    assert session_id == SESSION_ID
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/api/v1/sessions"
    assert request_json(requests[0]) == {"title": "Demo Session"}


def test_prepare_session_verifies_given_session_id() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=session_response())

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        session_id = prepare_session(client, SESSION_ID, "Ignored")

    assert session_id == SESSION_ID
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert requests[0].url.path == f"/api/v1/sessions/{SESSION_ID}"


def test_unknown_session_raises_clear_publisher_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, json={"detail": "Session not found"})
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError) as error:
            prepare_session(client, SESSION_ID, "Ignored")

    message = str(error.value)
    assert f"GET /api/v1/sessions/{SESSION_ID}" in message
    assert "HTTP 404" in message
    assert "Session not found" in message


def test_create_session_rejects_missing_response_fields() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(201, json={"title": "Missing ID"})
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError, match="gecersiz response formati"):
            create_session(client, "Demo")


def test_session_create_http_error_includes_endpoint_and_status() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(422, json={"detail": "invalid title"})
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError) as error:
            create_session(client, "")

    assert "POST /api/v1/sessions" in str(error.value)
    assert "HTTP 422" in str(error.value)


def test_existing_participants_are_listed_and_disconnected_are_filtered() -> None:
    response_data = [
        participant_response(PARTICIPANT_ID_1, status="authentic"),
        participant_response(DISCONNECTED_ID, status="disconnected"),
        participant_response(PARTICIPANT_ID_2, status="suspicious"),
    ]
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        participants = list_active_participants(client, SESSION_ID)

    assert [participant.participantId for participant in participants] == [
        PARTICIPANT_ID_1,
        PARTICIPANT_ID_2,
    ]


def test_only_missing_participant_count_is_created_with_backend_ids() -> None:
    requests: list[httpx.Request] = []
    created_ids = iter([PARTICIPANT_ID_2, PARTICIPANT_ID_3])

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(
                200,
                json=[
                    participant_response(PARTICIPANT_ID_1),
                    participant_response(DISCONNECTED_ID, status="disconnected"),
                ],
            )

        participant_id = next(created_ids)
        body = request_json(request)
        return httpx.Response(
            201,
            json=participant_response(
                participant_id,
                display_name=str(body["displayName"]),
            ),
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        participant_ids = prepare_participant_ids(client, SESSION_ID, 3)

    assert participant_ids == [PARTICIPANT_ID_1, PARTICIPANT_ID_2, PARTICIPANT_ID_3]
    post_requests = [request for request in requests if request.method == "POST"]
    assert len(post_requests) == 2
    assert [request_json(request) for request in post_requests] == [
        {"displayName": "Mock Participant 2"},
        {"displayName": "Mock Participant 3"},
    ]
    assert all(
        request.url.path == f"/api/v1/sessions/{SESSION_ID}/participants"
        for request in requests
    )


def test_no_participant_is_created_when_enough_active_participants_exist() -> None:
    methods: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        methods.append(request.method)
        return httpx.Response(
            200,
            json=[
                participant_response(PARTICIPANT_ID_1),
                participant_response(PARTICIPANT_ID_2),
                participant_response(PARTICIPANT_ID_3),
            ],
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        participant_ids = prepare_participant_ids(client, SESSION_ID, 2)

    assert participant_ids == [PARTICIPANT_ID_1, PARTICIPANT_ID_2]
    assert methods == ["GET"]


def test_participant_list_rejects_invalid_response_format() -> None:
    invalid_participant = participant_response(PARTICIPANT_ID_1)
    invalid_participant.pop("participantId")
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=[invalid_participant])
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError, match="participantId"):
            list_active_participants(client, SESSION_ID)


def test_participant_list_http_error_includes_endpoint_and_status() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(503, json={"detail": "unavailable"})
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError) as error:
            prepare_participant_ids(client, SESSION_ID, 1)

    assert f"GET /api/v1/sessions/{SESSION_ID}/participants" in str(error.value)
    assert "HTTP 503" in str(error.value)


def test_participant_create_http_error_includes_endpoint_and_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json=[])
        return httpx.Response(409, json={"detail": "cannot create participant"})

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError) as error:
            prepare_participant_ids(client, SESSION_ID, 1)

    assert f"POST /api/v1/sessions/{SESSION_ID}/participants" in str(error.value)
    assert "HTTP 409" in str(error.value)


def test_generated_request_matches_analysis_input_contract() -> None:
    payload = build_analysis_payload(
        session_id=SESSION_ID,
        participant_id=PARTICIPANT_ID_1,
        model_version="mock-model-v1",
        rng=random.Random(42),
        timestamp=FIXED_TIMESTAMP,
    )

    analysis_input = AnalysisInput.model_validate(payload)

    assert analysis_input.sessionId == SESSION_ID
    assert analysis_input.participantId == PARTICIPANT_ID_1
    assert analysis_input.modelVersion == "mock-model-v1"
    assert analysis_input.timestamp.tzinfo is not None


def test_same_seed_produces_same_score_sequence() -> None:
    def generate_scores(rng: random.Random) -> list[tuple[object, object]]:
        scores = []
        for _ in range(5):
            payload = build_analysis_payload(
                SESSION_ID,
                PARTICIPANT_ID_1,
                "mock-model-v1",
                rng,
                FIXED_TIMESTAMP,
            )
            scores.append((payload["fakeProbability"], payload["confidence"]))
        return scores

    assert generate_scores(random.Random(42)) == generate_scores(random.Random(42))


def test_generated_probabilities_are_between_zero_and_one() -> None:
    rng = random.Random(42)

    for _ in range(100):
        payload = build_analysis_payload(
            SESSION_ID,
            PARTICIPANT_ID_1,
            "mock-model-v1",
            rng,
            FIXED_TIMESTAMP,
        )

        assert 0.0 <= payload["fakeProbability"] <= 1.0
        assert 0.0 <= payload["confidence"] <= 1.0


def test_next_timestamp_strictly_increases_when_clock_does_not_advance() -> None:
    first = next_analysis_timestamp(None, FIXED_TIMESTAMP)
    second = next_analysis_timestamp(first, FIXED_TIMESTAMP)
    third = next_analysis_timestamp(second, FIXED_TIMESTAMP)

    assert first < second < third
    assert all(timestamp.tzinfo is timezone.utc for timestamp in [first, second, third])


def test_publish_uses_backend_participant_ids_and_increasing_timestamps(
    capsys: pytest.CaptureFixture[str],
) -> None:
    analysis_requests: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/api/v1/sessions":
            return httpx.Response(201, json=session_response())
        if request.method == "GET" and request.url.path.endswith("/participants"):
            return httpx.Response(
                200,
                json=[
                    participant_response(PARTICIPANT_ID_1),
                    participant_response(DISCONNECTED_ID, status="disconnected"),
                ],
            )
        if request.url.path.endswith("/participants"):
            return httpx.Response(
                201,
                json=participant_response(PARTICIPANT_ID_2),
            )
        if request.url.path == "/api/v1/analysis/evaluate":
            payload = request_json(request)
            analysis_requests.append(payload)
            return httpx.Response(200, json=analysis_response(payload))
        raise AssertionError(f"Unexpected request: {request.method} {request.url.path}")

    args = publisher.build_parser().parse_args(
        ["--participant-count", "2", "--iterations", "3", "--interval", "0"]
    )
    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        publisher.publish_samples(
            args,
            client,
            sleep_fn=lambda _: None,
            timestamp_fn=lambda: FIXED_TIMESTAMP,
        )

    participant_ids = {request["participantId"] for request in analysis_requests}
    assert participant_ids == {str(PARTICIPANT_ID_1), str(PARTICIPANT_ID_2)}
    assert str(DISCONNECTED_ID) not in participant_ids
    for participant_id in participant_ids:
        timestamps = [
            datetime.fromisoformat(str(request["timestamp"]))
            for request in analysis_requests
            if request["participantId"] == participant_id
        ]
        assert timestamps == sorted(timestamps)
        assert len(set(timestamps)) == 3
        assert all(timestamp.tzinfo is not None for timestamp in timestamps)

    output = capsys.readouterr().out
    assert f"sessionId={SESSION_ID} participantCount=2" in output
    assert output.count("realityScore=") == 6


def test_successful_analysis_response_is_validated_and_processed() -> None:
    payload = build_analysis_payload(
        SESSION_ID,
        PARTICIPANT_ID_1,
        "mock-model-v1",
        random.Random(42),
        FIXED_TIMESTAMP,
    )
    expected_response = analysis_response(payload)
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=expected_response)
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        response_data = post_analysis(client, payload)

    assert response_data == {
        **expected_response,
        "timestamp": "2026-01-15T12:30:00Z",
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("participantId", str(PARTICIPANT_ID_2)),
        ("realityScore", 1.5),
        ("status", "unknown"),
    ],
)
def test_invalid_analysis_response_raises_publisher_error(
    field: str,
    value: object,
) -> None:
    payload = build_analysis_payload(
        SESSION_ID,
        PARTICIPANT_ID_1,
        "mock-model-v1",
        random.Random(42),
        FIXED_TIMESTAMP,
    )
    response_data = analysis_response(payload)
    response_data[field] = value
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=response_data)
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError, match=field):
            post_analysis(client, payload)


def test_http_error_includes_endpoint_and_status() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(422, json={"detail": "invalid payload"})
    )

    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError) as error:
            post_analysis(client, {"participantId": str(PARTICIPANT_ID_1)})

    assert "POST /api/v1/analysis/evaluate" in str(error.value)
    assert "HTTP 422" in str(error.value)


def test_connection_error_becomes_publisher_error_without_leaking_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("password=super-secret", request=request)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport, base_url="http://testserver") as client:
        with pytest.raises(PublisherError) as error:
            prepare_session(client, SESSION_ID, "Ignored")

    assert "Backend baglanti hatasi" in str(error.value)
    assert f"GET /api/v1/sessions/{SESSION_ID}" in str(error.value)
    assert "super-secret" not in str(error.value)


@pytest.mark.parametrize("participant_count", ["0", "-1"])
def test_non_positive_participant_count_is_rejected(
    participant_count: str,
) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int(participant_count)


@pytest.mark.parametrize("interval", ["-0.1", "invalid"])
def test_invalid_interval_is_rejected(interval: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        non_negative_float(interval)


def test_main_returns_zero_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def successful_publish(*args: object, **kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(publisher, "publish_samples", successful_publish)

    exit_code = publisher.main(["--iterations", "1", "--interval", "0"])

    assert exit_code == 0
    assert called is True


def test_main_returns_one_on_publisher_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def failing_publish(*args: object, **kwargs: object) -> None:
        raise PublisherError("backend unavailable")

    monkeypatch.setattr(publisher, "publish_samples", failing_publish)

    exit_code = publisher.main(["--iterations", "1", "--interval", "0"])

    assert exit_code == 1
    assert "backend unavailable" in capsys.readouterr().err
