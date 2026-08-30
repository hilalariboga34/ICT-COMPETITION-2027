from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.session import SessionCreate, SessionResponse, SessionStatus


SESSION_ID = UUID("11111111-1111-4111-8111-111111111111")
UTC_TIMESTAMP = datetime(2026, 1, 15, 12, 30, tzinfo=timezone.utc)


def valid_session_response_data() -> dict[str, object]:
    return {
        "sessionId": SESSION_ID,
        "title": "Weekly Review",
        "status": "active",
        "createdAt": UTC_TIMESTAMP,
        "startedAt": UTC_TIMESTAMP,
        "endedAt": UTC_TIMESTAMP,
    }


def test_valid_session_create_is_accepted() -> None:
    session = SessionCreate(title="Weekly Review")

    assert session.title == "Weekly Review"


def test_session_create_strips_title_whitespace() -> None:
    session = SessionCreate(title="  Weekly Review  ")

    assert session.title == "Weekly Review"


@pytest.mark.parametrize("title", ["", "   "])
def test_session_create_rejects_blank_title(title: str) -> None:
    with pytest.raises(ValidationError):
        SessionCreate(title=title)


def test_session_create_rejects_title_longer_than_200_characters() -> None:
    with pytest.raises(ValidationError):
        SessionCreate(title="a" * 201)


def test_valid_session_response_is_accepted() -> None:
    session = SessionResponse(**valid_session_response_data())

    assert session.status is SessionStatus.ACTIVE


@pytest.mark.parametrize("field_name", ["createdAt", "startedAt", "endedAt"])
def test_session_response_rejects_datetime_without_timezone(
    field_name: str,
) -> None:
    data = valid_session_response_data()
    data[field_name] = datetime(2026, 1, 15, 12, 30)

    with pytest.raises(ValidationError):
        SessionResponse(**data)


def test_session_response_rejects_extra_field() -> None:
    data = valid_session_response_data()
    data["unexpectedField"] = "unexpected"

    with pytest.raises(ValidationError):
        SessionResponse(**data)


def test_session_response_rejects_invalid_status() -> None:
    data = valid_session_response_data()
    data["status"] = "invalid"

    with pytest.raises(ValidationError):
        SessionResponse(**data)
