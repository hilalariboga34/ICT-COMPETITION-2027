from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
ALLOWED_ORIGIN = "http://localhost:5173"
DISALLOWED_ORIGIN = "https://example.com"


def test_cors_preflight_allows_local_frontend_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_cors_preflight_does_not_allow_unknown_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": DISALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers


def test_health_endpoint_still_works_with_cors_enabled() -> None:
    response = client.get("/health")

    assert response.status_code == 200
