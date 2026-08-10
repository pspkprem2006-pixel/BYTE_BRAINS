"""Settings tests: DATABASE_URL normalization to the psycopg 3 dialect.

Hosts like Render provide postgres://, postgresql://, or
postgresql+psycopg2:// URLs; the app must rewrite those to
postgresql+psycopg:// so SQLAlchemy uses psycopg 3 (psycopg[binary]).
"""

import pytest

from app.core.config import Settings


@pytest.fixture
def settings_with_url(monkeypatch):
    """Build a fresh Settings with DATABASE_URL pinned to a value."""

    def _build(url: str) -> Settings:
        monkeypatch.setenv("DATABASE_URL", url)
        return Settings(_env_file=None)

    return _build


def test_postgres_url_normalized_to_psycopg3(settings_with_url) -> None:
    settings = settings_with_url("postgres://user:pass@host:5432/bytebrains")
    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/bytebrains"


def test_postgresql_url_normalized_to_psycopg3(settings_with_url) -> None:
    settings = settings_with_url("postgresql://user:pass@host:5432/bytebrains")
    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/bytebrains"


def test_postgresql_psycopg2_url_normalized_to_psycopg3(settings_with_url) -> None:
    settings = settings_with_url("postgresql+psycopg2://user:pass@host:5432/bytebrains")
    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/bytebrains"


def test_psycopg3_url_left_unchanged(settings_with_url) -> None:
    url = "postgresql+psycopg://user:pass@host:5432/bytebrains"
    settings = settings_with_url(url)
    assert settings.database_url == url


def test_percent_encoded_password_preserved(settings_with_url) -> None:
    settings = settings_with_url("postgres://user:p%40ss%3Aword@host:5432/bytebrains")
    assert settings.database_url == "postgresql+psycopg://user:p%40ss%3Aword@host:5432/bytebrains"


def test_empty_database_url_left_unchanged(settings_with_url) -> None:
    settings = settings_with_url("")
    assert settings.database_url == ""
