from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as DBSession

from app.db.session import get_db_session
from app.main import app
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


def test_create_session_returns_http_201(client: TestClient) -> None:
    response = client.post("/api/v1/sessions", json={"title": "Weekly Review"})

    assert response.status_code == 201


def test_create_session_returns_expected_fields(client: TestClient) -> None:
    response = client.post("/api/v1/sessions", json={"title": "Weekly Review"})
    body = response.json()

    assert UUID(body["sessionId"])
    assert body["title"] == "Weekly Review"
    assert body["status"] == "waiting"
    assert body["createdAt"] is not None
    assert body["startedAt"] is None
    assert body["endedAt"] is None


def test_create_session_persists_row(
    client: TestClient,
    db_session: DBSession,
) -> None:
    response = client.post("/api/v1/sessions", json={"title": "Weekly Review"})
    session_id = UUID(response.json()["sessionId"])

    persisted = db_session.get(SessionModel, session_id)

    assert persisted is not None
    assert persisted.title == "Weekly Review"


def test_create_session_trims_title(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sessions",
        json={"title": "  Weekly Review  "},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Weekly Review"


@pytest.mark.parametrize("title", ["", "   "])
def test_create_session_rejects_blank_title(
    client: TestClient,
    title: str,
) -> None:
    response = client.post("/api/v1/sessions", json={"title": title})

    assert response.status_code == 422


def test_create_session_rejects_extra_field(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sessions",
        json={"title": "Weekly Review", "unexpectedField": "unexpected"},
    )

    assert response.status_code == 422


def test_get_existing_session_returns_http_200(
    client: TestClient,
    db_session: DBSession,
) -> None:
    session = SessionModel(title="Weekly Review")
    db_session.add(session)
    db_session.flush()

    response = client.get(f"/api/v1/sessions/{session.id}")

    assert response.status_code == 200
    assert response.json()["sessionId"] == str(session.id)
    assert response.json()["title"] == "Weekly Review"


def test_get_unknown_session_returns_http_404(client: TestClient) -> None:
    response = client.get(f"/api/v1/sessions/{uuid4()}")

    assert response.status_code == 404


def test_get_invalid_uuid_returns_http_422(client: TestClient) -> None:
    response = client.get("/api/v1/sessions/not-a-uuid")

    assert response.status_code == 422
