"""Verify that the application and data layer import cleanly."""

from app.main import app
from app.models import Base


def test_app_imports() -> None:
    assert app.title == "ByteBrains API"


def test_all_tables_registered() -> None:
    expected = {
        "users",
        "subjects",
        "topics",
        "materials",
        "user_progress",
        "quiz_attempts",
        "study_plans",
        "study_tasks",
    }
    assert expected.issubset(Base.metadata.tables.keys())


def test_alembic_metadata_loaded() -> None:
    """Alembic's target metadata comes from the same Base as the models."""
    from app.models import Base as ModelBase

    assert Base is ModelBase