"""StudyTask model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class StudyTask(UUIDMixin, TimestampMixin, Base):
    """An individual task within a study plan."""

    __tablename__ = "study_tasks"

    study_plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("study_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Optional: a task may be linked to a topic.
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    study_plan: Mapped["StudyPlan"] = relationship(back_populates="tasks")
    topic: Mapped["Topic | None"] = relationship(back_populates="study_tasks")