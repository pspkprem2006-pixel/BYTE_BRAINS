"""UserProgress model."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UserProgress(UUIDMixin, TimestampMixin, Base):
    """A user's mastery of one topic.

    One row per user/topic combination (enforced by unique constraint),
    so repeated updates overwrite the same record instead of duplicating it.
    """

    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_progress_user_topic"),
        CheckConstraint(
            "mastery_score >= 0 AND mastery_score <= 100",
            name="ck_user_progress_mastery_range",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )
    # Percentage score 0-100 reflecting mastery of the topic.
    mastery_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    topics_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_studied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="progress")
    topic: Mapped["Topic"] = relationship(back_populates="progress")