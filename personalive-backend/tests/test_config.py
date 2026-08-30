import pytest
from pydantic import ValidationError

from app.core.config import Settings


EXPECTED_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:1420",
    "http://127.0.0.1:1420",
]


def default_settings() -> Settings:
    return Settings(_env_file=None)


def test_default_app_name() -> None:
    assert default_settings().app_name == "PersonaLive API"


def test_default_app_version() -> None:
    assert default_settings().app_version == "0.1.0"


def test_default_authentic_threshold() -> None:
    assert default_settings().authentic_threshold == pytest.approx(0.60)


@pytest.mark.parametrize("threshold", [-0.01, 1.01])
def test_authentic_threshold_outside_range_is_rejected(threshold: float) -> None:
    with pytest.raises(ValidationError):
        Settings(authentic_threshold=threshold, _env_file=None)


def test_invalid_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="development", _env_file=None)


def test_default_cors_origins() -> None:
    assert default_settings().cors_origins == EXPECTED_CORS_ORIGINS
