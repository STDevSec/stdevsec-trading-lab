"""Environment-based configuration (12-factor). No secrets are hardcoded."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="API_", env_file=".env", extra="ignore")

    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    # CORS origins as a comma-separated string in the env; parsed to a list.
    cors_origins: str = "http://localhost:3000"
    # SQLAlchemy URL. Defaults to local Postgres; tests override with SQLite.
    database_url: str = "postgresql+psycopg://trading_lab:change_me_in_local_only@localhost:5432/trading_lab"
    # Reject dataset uploads with more candles than this (resource exhaustion).
    max_candles: int = 200_000
    # Cap raw CSV upload size in bytes before parsing (resource exhaustion). 50 MiB.
    max_upload_bytes: int = 50 * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
