"""Application settings.

Values are loaded from environment variables, with ".env" as a fallback.
Never hardcode secrets: put real values in a local ".env" file
(see ".env.example") and keep that file out of version control.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings."""

    app_name: str = "ByteBrains API"
    app_version: str = "0.1.0"

    # PostgreSQL connection string.
    database_url: str = ""

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Force the psycopg 3 dialect for any PostgreSQL URL.

        Hosts like Render supply postgres://, postgresql://, or
        postgresql+psycopg2:// URLs, which SQLAlchemy maps to the psycopg2
        driver. This project installs psycopg 3 (psycopg[binary]), so the
        scheme is rewritten to postgresql+psycopg:// up front — the rest of
        the URL (including passwords with percent-encoding) is untouched.
        """
        if not value:
            return value
        for scheme in ("postgresql+psycopg2://", "postgresql://", "postgres://"):
            if value.startswith(scheme):
                return "postgresql+psycopg://" + value[len(scheme):]
        return value

    # OpenRouter AI Tutor settings.
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.5-flash"

    # Brave Web Search settings.
    # The key is used server-side only and must never reach frontend code.
    # When it is missing the application still starts; web search calls then
    # fail with a controlled "web search not configured" error.
    brave_search_api_key: str = ""
    web_search_enabled: bool = True
    web_search_timeout_seconds: float = 10.0
    web_search_max_results: int = 5

    @field_validator("web_search_timeout_seconds")
    @classmethod
    def clamp_search_timeout(cls, value: float) -> float:
        """Keep the provider timeout within safe bounds instead of crashing."""
        return max(1.0, min(value, 30.0))

    @field_validator("web_search_max_results")
    @classmethod
    def clamp_search_max_results(cls, value: int) -> int:
        """Never allow more than 10 results per search request."""
        return max(1, min(value, 10))

    # Learning-resource discovery settings.
    # Comma-separated list of domains whose results may be marked "official".
    # Match is on the registrable domain only (www subdomains are handled).
    # Keep this list small and maintainable; nothing is official unless it is
    # listed here.
    web_search_trusted_domains: str = "postgresql.org,python.org,nodejs.org"

    # How many query variants the learning-resource discovery runs at most
    # (e.g. "<topic>", "<topic> tutorial", "<topic> official documentation").
    # Keeps search usage controlled per request.
    web_search_learning_max_queries: int = 4

    @field_validator("web_search_learning_max_queries")
    @classmethod
    def clamp_learning_max_queries(cls, value: int) -> int:
        """Never run more than 5 query variants per discovery request."""
        return max(1, min(value, 5))

    # Allowed CORS origins, comma-separated (e.g. the Vercel frontend URL).
    # Local development defaults to the Vite dev server.
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()