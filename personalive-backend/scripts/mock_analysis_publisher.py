from __future__ import annotations

import argparse
import random
import sys
import time
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from typing import Any, TypeVar
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from app.schemas.analysis import AnalysisResult, ParticipantStatus
from app.schemas.participant import ParticipantResponse
from app.schemas.session import SessionResponse


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_SESSION_TITLE = "Mock Analysis Session"
SESSIONS_PATH = "/api/v1/sessions"
EVALUATE_PATH = "/api/v1/analysis/evaluate"

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class PublisherError(RuntimeError):
    """Mock publisher calistirilirken olusan anlasilir hata."""


def positive_int(value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("pozitif bir tam sayi olmalidir") from exc

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("pozitif bir tam sayi olmalidir")
    return parsed_value


def non_negative_float(value: str) -> float:
    try:
        parsed_value = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("negatif olmayan bir sayi olmalidir") from exc

    if parsed_value < 0.0:
        raise argparse.ArgumentTypeError("negatif olmayan bir sayi olmalidir")
    return parsed_value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Local gelistirme icin backend'de session ve participant hazirlayip "
            "ornek PersonaLive analiz verisi yayinlar."
        )
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Backend adresi (varsayilan: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--session-id",
        type=UUID,
        default=None,
        help="Kullanilacak mevcut session UUID'si; verilmezse yeni session olusturulur",
    )
    parser.add_argument(
        "--session-title",
        default=DEFAULT_SESSION_TITLE,
        help=(
            "Yeni session basligi "
            f"(varsayilan: {DEFAULT_SESSION_TITLE!r}; --session-id ile kullanilmaz)"
        ),
    )
    parser.add_argument(
        "--participant-count",
        type=positive_int,
        default=3,
        help="Analiz gonderilecek aktif participant sayisi (varsayilan: 3)",
    )
    parser.add_argument(
        "--iterations",
        type=positive_int,
        default=10,
        help="Her participant icin analiz sayisi (varsayilan: 10)",
    )
    parser.add_argument(
        "--interval",
        type=non_negative_float,
        default=2.0,
        help="Iteration'lar arasindaki bekleme saniyesi (varsayilan: 2.0)",
    )
    parser.add_argument(
        "--model-version",
        default="mock-model-v1",
        help="Analiz model version metni (varsayilan: mock-model-v1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic skorlar icin random seed (varsayilan: 42)",
    )
    return parser


def _request_json(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    json: dict[str, object] | None = None,
) -> Any:
    try:
        response = client.request(method, path, json=json)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip()
        message = f"{method} {path} HTTP {exc.response.status_code} hatasi"
        if detail:
            message = f"{message}: {detail}"
        raise PublisherError(message) from exc
    except httpx.RequestError as exc:
        # Exception metni URL icinde credentials barindirabilir; endpoint
        # bilgisi yeterli ve guvenli oldugu icin yalnizca hata turunu yaziyoruz.
        raise PublisherError(
            f"Backend baglanti hatasi ({method} {path}, {type(exc).__name__})"
        ) from exc

    try:
        return response.json()
    except ValueError as exc:
        raise PublisherError(
            f"{method} {path} gecerli bir JSON response dondurmedi"
        ) from exc


def _validate_response(
    response_data: object,
    model_type: type[ResponseModel],
    *,
    endpoint: str,
) -> ResponseModel:
    try:
        return model_type.model_validate(response_data)
    except ValidationError as exc:
        invalid_fields = sorted(
            {str(error["loc"][0]) for error in exc.errors() if error["loc"]}
        )
        field_detail = ", ".join(invalid_fields) or "response body"
        raise PublisherError(
            f"{endpoint} gecersiz response formati: {field_detail}"
        ) from exc


def create_session(client: httpx.Client, title: str) -> UUID:
    response_data = _request_json(
        client,
        "POST",
        SESSIONS_PATH,
        json={"title": title},
    )
    session = _validate_response(
        response_data,
        SessionResponse,
        endpoint=f"POST {SESSIONS_PATH}",
    )
    return session.sessionId


def verify_session(client: httpx.Client, session_id: UUID) -> UUID:
    path = f"{SESSIONS_PATH}/{session_id}"
    response_data = _request_json(client, "GET", path)
    session = _validate_response(
        response_data,
        SessionResponse,
        endpoint=f"GET {path}",
    )
    if session.sessionId != session_id:
        raise PublisherError(
            f"GET {path} farkli sessionId dondurdu: {session.sessionId}"
        )
    return session.sessionId


def prepare_session(
    client: httpx.Client,
    session_id: UUID | None,
    session_title: str,
) -> UUID:
    if session_id is None:
        return create_session(client, session_title)
    return verify_session(client, session_id)


def list_active_participants(
    client: httpx.Client,
    session_id: UUID,
) -> list[ParticipantResponse]:
    path = f"{SESSIONS_PATH}/{session_id}/participants"
    response_data = _request_json(client, "GET", path)
    if not isinstance(response_data, list):
        raise PublisherError(f"GET {path} response JSON listesi olmalidir")

    participants: list[ParticipantResponse] = []
    for index, item in enumerate(response_data):
        participant = _validate_response(
            item,
            ParticipantResponse,
            endpoint=f"GET {path} participant[{index}]",
        )
        if participant.sessionId != session_id:
            raise PublisherError(
                f"GET {path} participant[{index}] farkli sessionId dondurdu"
            )
        if participant.status is not ParticipantStatus.DISCONNECTED:
            participants.append(participant)
    return participants


def create_participant(
    client: httpx.Client,
    session_id: UUID,
    display_name: str,
) -> ParticipantResponse:
    path = f"{SESSIONS_PATH}/{session_id}/participants"
    response_data = _request_json(
        client,
        "POST",
        path,
        json={"displayName": display_name},
    )
    participant = _validate_response(
        response_data,
        ParticipantResponse,
        endpoint=f"POST {path}",
    )
    if participant.sessionId != session_id:
        raise PublisherError(f"POST {path} farkli sessionId dondurdu")
    if participant.status is ParticipantStatus.DISCONNECTED:
        raise PublisherError(f"POST {path} disconnected participant dondurdu")
    return participant


def prepare_participant_ids(
    client: httpx.Client,
    session_id: UUID,
    participant_count: int,
) -> list[UUID]:
    active_participants = list_active_participants(client, session_id)
    missing_count = max(0, participant_count - len(active_participants))

    for participant_number in range(
        len(active_participants) + 1,
        len(active_participants) + missing_count + 1,
    ):
        active_participants.append(
            create_participant(
                client,
                session_id,
                f"Mock Participant {participant_number}",
            )
        )

    return [
        participant.participantId
        for participant in active_participants[:participant_count]
    ]


def next_analysis_timestamp(
    previous_timestamp: datetime | None,
    current_timestamp: datetime | None = None,
) -> datetime:
    generated_at = current_timestamp or datetime.now(timezone.utc)
    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise ValueError("timestamp timezone bilgisi icermelidir")

    generated_at = generated_at.astimezone(timezone.utc)
    if previous_timestamp is not None and generated_at <= previous_timestamp:
        return previous_timestamp + timedelta(microseconds=1)
    return generated_at


def build_analysis_payload(
    session_id: UUID,
    participant_id: UUID,
    model_version: str,
    rng: random.Random,
    timestamp: datetime | None = None,
) -> dict[str, object]:
    generated_at = timestamp or datetime.now(timezone.utc)
    if generated_at.tzinfo is None or generated_at.utcoffset() is None:
        raise ValueError("timestamp timezone bilgisi icermelidir")

    return {
        "sessionId": str(session_id),
        "participantId": str(participant_id),
        "fakeProbability": rng.random(),
        "confidence": rng.random(),
        "timestamp": generated_at.astimezone(timezone.utc).isoformat(),
        "modelVersion": model_version,
    }


def post_analysis(
    client: httpx.Client,
    payload: dict[str, object],
) -> dict[str, object]:
    response_data = _request_json(
        client,
        "POST",
        EVALUATE_PATH,
        json=payload,
    )
    result = _validate_response(
        response_data,
        AnalysisResult,
        endpoint=f"POST {EVALUATE_PATH}",
    )

    try:
        expected_participant_id = UUID(str(payload["participantId"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise PublisherError("Analysis payload participantId alani gecersiz") from exc
    if result.participantId != expected_participant_id:
        raise PublisherError(
            f"POST {EVALUATE_PATH} farkli participantId dondurdu: "
            f"{result.participantId}"
        )

    return result.model_dump(mode="json")


def publish_samples(
    args: argparse.Namespace,
    client: httpx.Client,
    sleep_fn: Callable[[float], None] = time.sleep,
    timestamp_fn: Callable[[], datetime] | None = None,
) -> None:
    rng = random.Random(args.seed)
    session_id = prepare_session(client, args.session_id, args.session_title)
    participant_ids = prepare_participant_ids(
        client,
        session_id,
        args.participant_count,
    )
    print(f"sessionId={session_id} participantCount={len(participant_ids)}")

    previous_timestamps: dict[UUID, datetime] = {}
    clock = timestamp_fn or (lambda: datetime.now(timezone.utc))

    for iteration_index in range(args.iterations):
        for participant_id in participant_ids:
            timestamp = next_analysis_timestamp(
                previous_timestamps.get(participant_id),
                clock(),
            )
            previous_timestamps[participant_id] = timestamp
            payload = build_analysis_payload(
                session_id=session_id,
                participant_id=participant_id,
                model_version=args.model_version,
                rng=rng,
                timestamp=timestamp,
            )
            response_data = post_analysis(client, payload)
            print(
                f"[{iteration_index + 1}/{args.iterations}] "
                f"participantId={response_data['participantId']} "
                f"realityScore={response_data['realityScore']} "
                f"status={response_data['status']}"
            )

        if iteration_index < args.iterations - 1:
            sleep_fn(args.interval)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        with httpx.Client(
            base_url=args.base_url.rstrip("/"),
            timeout=10.0,
        ) as client:
            publish_samples(args, client)
    except (PublisherError, ValueError) as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
