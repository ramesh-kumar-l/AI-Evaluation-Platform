"""Typed application settings (12-factor, env-driven, offline-first defaults)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo-local path used for the zero-infra SQLite fallback.
_DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[2] / "var" / "aep.db"


class Settings(BaseSettings):
    """All runtime configuration. Values come from environment / .env."""

    model_config = SettingsConfigDict(
        env_prefix="AEP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["local", "test", "production"] = "local"
    service_name: str = "aep-backend"

    log_level: str = "INFO"
    log_json: bool = False

    # Empty => offline SQLite fallback (see database_url property).
    database_url: str = ""

    ollama_base_url: str = "http://localhost:11434"
    enable_cloud_providers: bool = False

    # Telemetry is opt-in; populated from the standard OTel env var if present.
    otel_exporter_otlp_endpoint: str = Field(default="", alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    @property
    def resolved_database_url(self) -> str:
        """Return the configured DB URL, or an offline SQLite fallback when unset."""
        if self.database_url:
            return self.database_url
        _DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+pysqlite:///{_DEFAULT_SQLITE_PATH.as_posix()}"

    @property
    def telemetry_enabled(self) -> bool:
        return bool(self.otel_exporter_otlp_endpoint)


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (one instance per process)."""
    return Settings()
