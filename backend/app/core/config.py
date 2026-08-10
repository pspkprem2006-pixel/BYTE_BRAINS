"""Application settings.

Values are loaded from environment variables, with ".env" as a fallback.
Never hardcode secrets: put real values in a local ".env" file
(see ".env.example") and keep that file out of version control.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings."""

    app_name: str = "ByteBrains API"
    app_version: str = "0.1.0"

    # PostgreSQL connection string. Kept empty during Phase 1;
    # it will be configured in the database phase.
    database_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()