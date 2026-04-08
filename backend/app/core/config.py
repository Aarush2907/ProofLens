from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> repository root is three levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Runtime configuration loaded from the environment and the root .env file.

    Environment variables win over the file, which is what lets tests point at
    a temporary database without editing a developer's local .env.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ProofLens"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = (
        "postgresql+psycopg://prooflens:prooflens@localhost:5432/prooflens"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
