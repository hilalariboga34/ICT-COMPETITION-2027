import argparse
import random
import sys
import time
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from uuid import UUID, uuid5

import httpx


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
EVALUATE_PATH = "/api/v1/analysis/evaluate"


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
        description="Local gelistirme icin ornek PersonaLive analiz verisi yayinlar."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--session-id", type=UUID, default=DEFAULT_SESSION_ID)
    parser.add_argument("--participant-count", type=positive_int, default=3)
    parser.add_argument("--iterations", type=positive_int, default=10)
    parser.add_argument("--interval", type=non_negative_float, default=2.0)
    parser.add_argument("--model-version", default="mock-model-v1")
    parser.add_argument("--seed", type=int, default=42)
    return parser


def generate_participant_ids(
    session_id: UUID,
    participant_count: int,
) -> list[UUID]:
    return [
        uuid5(session_id, f"participant-{participant_number}")
        for participant_number in range(1, participant_count + 1)
    ]


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
    try:
        response = client.post(EVALUATE_PATH, json=payload)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip()
        message = f"Backend HTTP {exc.response.status_code} hatasi"
        if detail:
            message = f"{message}: {detail}"
        raise PublisherError(message) from exc
    except httpx.RequestError as exc:
        raise PublisherError(f"Backend baglanti hatasi: {exc}") from exc

    try:
        response_data = response.json()
    except ValueError as exc:
        raise PublisherError("Backend gecerli bir JSON response dondurmedi") from exc

    if not isinstance(response_data, dict):
        raise PublisherError("Backend response JSON nesnesi olmalidir")

    required_fields = ("participantId", "realityScore", "status")
    missing_fields = [field for field in required_fields if field not in response_data]
    if missing_fields:
        raise PublisherError(
            "Backend response alanlari eksik: " + ", ".join(missing_fields)
        )

    return response_data


def publish_samples(
    args: argparse.Namespace,
    client: httpx.Client,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> None:
    rng = random.Random(args.seed)
    participant_ids = generate_participant_ids(
        args.session_id,
        args.participant_count,
    )

    for iteration_index in range(args.iterations):
        for participant_id in participant_ids:
            payload = build_analysis_payload(
                session_id=args.session_id,
                participant_id=participant_id,
                model_version=args.model_version,
                rng=rng,
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
