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

    # PostgreSQL connection string.
    database_url: str = ""

    # OpenRouter AI Tutor settings.
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()