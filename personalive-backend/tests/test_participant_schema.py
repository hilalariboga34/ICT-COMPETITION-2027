from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.analysis import ParticipantStatus
from app.schemas.participant import ParticipantCreate, ParticipantResponse


SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
PARTICIPANT_ID = UUID("22222222-2222-4222-8222-222222222222")
UTC_TIMESTAMP = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)


def valid_participant_response_data() -> dict[str, object]:
    return {
        "participantId": PARTICIPANT_ID,
        "sessionId": SESSION_ID,
        "displayName": "Ada Lovelace",
        "status": "authentic",
        "joinedAt": UTC_TIMESTAMP,
        "leftAt": UTC_TIMESTAMP,
    }


def test_valid_participant_create_is_accepted() -> None:
    participant = ParticipantCreate(displayName="Ada Lovelace")

    assert participant.displayName == "Ada Lovelace"


def test_participant_create_strips_display_name_whitespace() -> None:
    participant = ParticipantCreate(displayName="  Ada Lovelace  ")

    assert participant.displayName == "Ada Lovelace"


@pytest.mark.parametrize("display_name", ["", "   "])
def test_participant_create_rejects_blank_display_name(display_name: str) -> None:
    with pytest.raises(ValidationError):
        ParticipantCreate(displayName=display_name)


def test_participant_create_rejects_name_longer_than_100_characters() -> None:
    with pytest.raises(ValidationError):
        ParticipantCreate(displayName="a" * 101)


def test_valid_participant_response_is_accepted() -> None:
    participant = ParticipantResponse(**valid_participant_response_data())

    assert participant.participantId == PARTICIPANT_ID


@pytest.mark.parametrize("status", [status.value for status in ParticipantStatus])
def test_participant_response_accepts_existing_status_values(status: str) -> None:
    data = valid_participant_response_data()
    data["status"] = status

    participant = ParticipantResponse(**data)

    assert participant.status.value == status


@pytest.mark.parametrize("field_name", ["joinedAt", "leftAt"])
def test_participant_response_rejects_datetime_without_timezone(
    field_name: str,
) -> None:
    data = valid_participant_response_data()
    data[field_name] = datetime(2026, 1, 15, 12, 30)

    with pytest.raises(ValidationError):
        ParticipantResponse(**data)


def test_participant_response_rejects_extra_field() -> None:
    data = valid_participant_response_data()
    data["unexpectedField"] = "unexpected"

    with pytest.raises(ValidationError):
        ParticipantResponse(**data)
