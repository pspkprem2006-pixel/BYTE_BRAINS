"""StudyPlan model."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class StudyPlan(UUIDMixin, TimestampMixin, Base):
    """A study plan belonging to one user, containing study tasks."""

    __tablename__ = "study_plans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)

    user: Mapped["User"] = relationship(back_populates="study_plans")
    tasks: Mapped[list["StudyTask"]] = relationship(
        back_populates="study_plan",
        cascade="all, delete-orphan",
        order_by="StudyTask.scheduled_at",
    )