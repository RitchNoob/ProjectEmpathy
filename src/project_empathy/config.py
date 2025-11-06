"""Configuration models for the Project Empathy backend."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database connectivity details."""

    url: str = Field(
        default="sqlite:///./empathy.db",
        description="SQLAlchemy database URL. Defaults to a local SQLite database.",
    )
    echo: bool = Field(default=False, description="Enable SQL logging for debugging.")


class TwilioSettings(BaseModel):
    """Twilio account configuration."""

    account_sid: str = Field(default="", description="Twilio Account SID")
    auth_token: str = Field(default="", description="Twilio Auth Token")
    voice_phone_number: str = Field(default="", description="Provisioned Twilio number")
    status_callback_url: Optional[HttpUrl] = Field(
        default=None, description="Optional callback URL for call status updates."
    )


class OpenAISettings(BaseModel):
    """Large language model integration settings."""

    api_key: str = Field(default="", description="OpenAI API key or compatible provider key")
    model: str = Field(
        default="gpt-4o-mini",
        description="Chat completion model identifier (OpenAI or equivalent).",
    )
    request_timeout: int = Field(default=60, description="Timeout in seconds for API calls.")


class FlexpriceSettings(BaseModel):
    """Flexprice subscription platform configuration."""

    base_url: HttpUrl = Field(default="https://api.flexprice.io", description="Flexprice API base URL")
    api_key: str = Field(default="", description="Flexprice API token")
    product_id: Optional[str] = Field(
        default=None,
        description="Optional Flexprice product identifier to associate plans with.",
    )


class StorageSettings(BaseModel):
    """Paths for exported assets."""

    data_dir: Path = Field(default=Path("data"), description="Directory for structured data.")
    transcripts_dir: Path = Field(
        default=Path("data/transcripts"), description="Directory for stored call transcripts."
    )

    @validator("data_dir", "transcripts_dir", pre=True)
    def _ensure_path(cls, value: Path | str) -> Path:
        return Path(value)


class ApplicationSettings(BaseSettings):
    """Top-level configuration for the backend service."""

    debug: bool = Field(default=False, description="Enable FastAPI debug mode")
    secret_key: str = Field(
        default="change-me", description="Secret key for session signing and auth tokens"
    )
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS origins")

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    twilio: TwilioSettings = Field(default_factory=TwilioSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    flexprice: FlexpriceSettings = Field(default_factory=FlexpriceSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)

    model_config = SettingsConfigDict(env_nested_delimiter="__", env_prefix="EMP_", env_file=".env")


@lru_cache
def get_settings() -> ApplicationSettings:
    """Return cached application settings."""

    return ApplicationSettings()


__all__ = ["ApplicationSettings", "get_settings"]
