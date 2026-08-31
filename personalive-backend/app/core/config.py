from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    app_name: str = "PersonaLive API"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "production"] = "local"
    authentic_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:1420",
            "http://127.0.0.1:1420",
        ]
    )
    database_url: str | None = Field(default=None)
    # Sadece tests/test_migrations.py için: downgrade/upgrade döngüsü
    # DESTRUCTIVE olduğundan ayrı bir veritabanına yönlendirilir, asıl
    # DATABASE_URL'e asla dokunmaz (bkz. DATABASE.md).
    test_database_url: str | None = Field(default=None)


@lru_cache
def get_settings() -> Settings:
    return Settings()
