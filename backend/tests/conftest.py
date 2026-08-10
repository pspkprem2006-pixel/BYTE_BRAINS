"""Pytest setup: run the test suite against an ISOLATED database.

The dev database (bytebrains) is never touched. Tests use
"bytebrains_test", derived from the same .env credentials:

1. read DATABASE_URL from backend/.env
2. swap the database name to bytebrains_test
3. create that database if it does not exist yet
4. apply Alembic migrations to it
5. point the app at it via the DATABASE_URL environment variable
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEST_DATABASE_NAME = "bytebrains_test"

# Ensure .env and alembic.ini resolve regardless of where pytest was started.
os.chdir(BACKEND_DIR)

# pytest imports this module before any test module, so setting the
# environment variable here guarantees the app connects to the test database.
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def _load_database_url() -> str:
    """Read DATABASE_URL from backend/.env (without importing the app)."""
    env_file = BACKEND_DIR / ".env"
    for line in env_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("DATABASE_URL="):
            return stripped.split("=", 1)[1].strip()
    raise RuntimeError("DATABASE_URL not found in backend/.env")


def _render_url(url) -> str:
    """Render a SQLAlchemy URL as a string WITHOUT masking the password.

    ``str(url)`` would mask it as ``***``, which breaks connecting.
    """
    return url.render_as_string(hide_password=False)


def _ensure_test_database(test_url: str) -> None:
    """Create the test database if it does not exist yet."""
    server_url = make_url(test_url).set(database="postgres")
    engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DATABASE_NAME},
        ).first()
        if exists is None:
            connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE_NAME}"'))
    engine.dispose()


def _apply_migrations(test_url: str) -> None:
    from alembic import command
    from alembic.config import Config

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option(
        "sqlalchemy.url", test_url.replace("%", "%%")
    )
    command.upgrade(config, "head")


_test_url = _render_url(make_url(_load_database_url()).set(database=TEST_DATABASE_NAME))
os.environ["DATABASE_URL"] = _test_url

_ensure_test_database(_test_url)
_apply_migrations(_test_url)