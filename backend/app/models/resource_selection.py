"""LearningResourceSelection model.

A web learning resource the student explicitly chose to learn from. Only
the search-provider metadata (title, snippet, type, ...) is stored — never
fetched page content, credentials, or raw provider payloads.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

RESOURCE_TYPE_VALUES = (
    "official_docs",
    "tutorial",
    "article",
    "video",
    "practice",
    "reference",
    "course",
    "other",
)
DIFFICULTY_VALUES = ("beginner", "intermediate", "advanced")


class LearningResourceSelection(UUIDMixin, TimestampMixin, Base):
    """One user-selected web learning resource."""

    __tablename__ = "learning_resource_selections"
    __table_args__ = (
        CheckConstraint(
            "resource_type IN "
            "('official_docs','tutorial','article','video','practice',"
            "'reference','course','other')",
            name="ck_learning_resources_resource_type",
        ),
        CheckConstraint(
            "difficulty IN ('beginner','intermediate','advanced') OR difficulty IS NULL",
            name="ck_learning_resources_difficulty",
        ),
        UniqueConstraint(
            "user_id", "url", name="uq_learning_resources_user_url"
        ),
        Index(
            "ix_learning_resources_user_created",
            "user_id",
            "created_at",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    resource_type: Mapped[str] = mapped_column(
        String(50), default="other", nullable=False
    )
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="web_search", nullable=False)
    # Bumped whenever the resource is included in an AI learning context.
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    owner: Mapped["User"] = relationship(back_populates="resource_selections")
    subject: Mapped["Subject | None"] = relationship(
        back_populates="resource_selections"
    )