from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db_session
from app.main import app
from app.models.participant import Participant
from app.models.session import Session as SessionModel
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


# --- create ---------------------------------------------------------------


def test_create_participant_returns_http_201(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )

    assert response.status_code == 201


def test_create_participant_returns_expected_fields(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    body = response.json()

    assert UUID(body["participantId"])
    assert body["sessionId"] == str(session.id)
    assert body["displayName"] == "Ayşe"
    assert body["status"] == "analyzing"
    assert body["joinedAt"] is not None
    assert body["leftAt"] is None


def test_create_participant_persists_row(
    client: TestClient,
    db_session: DBSession,
    session: SessionModel,
) -> None:
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = UUID(response.json()["participantId"])

    persisted = db_session.get(Participant, participant_id)

    assert persisted is not None
    assert persisted.display_name == "Ayşe"
    assert persisted.session_id == session.id


def test_create_participant_trims_display_name(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "  Ayşe  "},
    )

    assert response.status_code == 201
    assert response.json()["displayName"] == "Ayşe"


@pytest.mark.parametrize("display_name", ["", "   "])
def test_create_participant_rejects_blank_display_name(
    client: TestClient, session: SessionModel, display_name: str
) -> None:
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": display_name},
    )

    assert response.status_code == 422


def test_create_participant_rejects_extra_field(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe", "unexpectedField": "unexpected"},
    )

    assert response.status_code == 422


def test_create_participant_for_unknown_session_returns_http_404(
    client: TestClient,
) -> None:
    response = client.post(
        f"/api/v1/sessions/{uuid4()}/participants",
        json={"displayName": "Ayşe"},
    )

    assert response.status_code == 404


def test_create_participant_invalid_session_uuid_returns_http_422(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/sessions/not-a-uuid/participants",
        json={"displayName": "Ayşe"},
    )

    assert response.status_code == 422


# --- list -------------------------------------------------------------


def test_list_participants_returns_created_participants(
    client: TestClient, session: SessionModel
) -> None:
    client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Mehmet"},
    )

    response = client.get(f"/api/v1/sessions/{session.id}/participants")

    assert response.status_code == 200
    names = {p["displayName"] for p in response.json()}
    assert names == {"Ayşe", "Mehmet"}


def test_list_participants_returns_empty_list_when_none_joined(
    client: TestClient, session: SessionModel
) -> None:
    response = client.get(f"/api/v1/sessions/{session.id}/participants")

    assert response.status_code == 200
    assert response.json() == []


def test_list_participants_does_not_leak_other_sessions(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    other_session = SessionModel(title="Other")
    db_session.add(other_session)
    db_session.flush()
    client.post(
        f"/api/v1/sessions/{other_session.id}/participants",
        json={"displayName": "Fatma"},
    )

    response = client.get(f"/api/v1/sessions/{session.id}/participants")

    assert response.status_code == 200
    assert response.json() == []


def test_list_participants_for_unknown_session_returns_http_404(
    client: TestClient,
) -> None:
    response = client.get(f"/api/v1/sessions/{uuid4()}/participants")

    assert response.status_code == 404


def test_list_participants_invalid_session_uuid_returns_http_422(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/sessions/not-a-uuid/participants")

    assert response.status_code == 422


# --- disconnect ---------------------------------------------------------


def test_disconnect_participant_returns_http_200(
    client: TestClient, session: SessionModel
) -> None:
    create_response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = create_response.json()["participantId"]

    response = client.post(
        f"/api/v1/sessions/{session.id}/participants/{participant_id}/disconnect"
    )

    assert response.status_code == 200


def test_disconnect_participant_sets_status_and_left_at(
    client: TestClient, session: SessionModel
) -> None:
    create_response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = create_response.json()["participantId"]

    response = client.post(
        f"/api/v1/sessions/{session.id}/participants/{participant_id}/disconnect"
    )
    body = response.json()

    assert body["status"] == "disconnected"
    assert body["leftAt"] is not None


def test_disconnect_participant_is_idempotent(
    client: TestClient, session: SessionModel
) -> None:
    create_response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = create_response.json()["participantId"]
    url = f"/api/v1/sessions/{session.id}/participants/{participant_id}/disconnect"

    first_response = client.post(url)
    second_response = client.post(url)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["leftAt"] == second_response.json()["leftAt"]


def test_disconnect_participant_does_not_delete_row(
    client: TestClient,
    db_session: DBSession,
    session: SessionModel,
) -> None:
    create_response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = UUID(create_response.json()["participantId"])

    client.post(
        f"/api/v1/sessions/{session.id}/participants/{participant_id}/disconnect"
    )

    persisted = db_session.get(Participant, participant_id)
    assert persisted is not None
    assert persisted.display_name == "Ayşe"


def test_disconnect_participant_for_unknown_session_returns_http_404(
    client: TestClient, session: SessionModel
) -> None:
    create_response = client.post(
        f"/api/v1/sessions/{session.id}/participants",
        json={"displayName": "Ayşe"},
    )
    participant_id = create_response.json()["participantId"]

    response = client.post(
        f"/api/v1/sessions/{uuid4()}/participants/{participant_id}/disconnect"
    )

    assert response.status_code == 404


def test_disconnect_unknown_participant_returns_http_404(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants/{uuid4()}/disconnect"
    )

    assert response.status_code == 404


def test_disconnect_participant_from_other_session_returns_http_404(
    client: TestClient, db_session: DBSession, session: SessionModel
) -> None:
    other_session = SessionModel(title="Other")
    db_session.add(other_session)
    db_session.flush()
    create_response = client.post(
        f"/api/v1/sessions/{other_session.id}/participants",
        json={"displayName": "Fatma"},
    )
    participant_id = create_response.json()["participantId"]

    # participant, other_session'a ait ama session'ın URL'i üzerinden
    # disconnect edilmeye çalışılıyor — 404 dönmeli.
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants/{participant_id}/disconnect"
    )

    assert response.status_code == 404


def test_disconnect_invalid_participant_uuid_returns_http_422(
    client: TestClient, session: SessionModel
) -> None:
    response = client.post(
        f"/api/v1/sessions/{session.id}/participants/not-a-uuid/disconnect"
    )

    assert response.status_code == 422
