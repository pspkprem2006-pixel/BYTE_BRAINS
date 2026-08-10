"""Topic model."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Topic(UUIDMixin, TimestampMixin, Base):
    """A topic inside a subject (e.g. "Normalization" inside DBMS)."""

    __tablename__ = "topics"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # 0-based display order of the topic within the subject.
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="topics")

    progress: Mapped[list["UserProgress"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )
    # Quiz attempts and study tasks survive a topic deletion with a NULL link.
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="topic", passive_deletes=True
    )
    study_tasks: Mapped[list["StudyTask"]] = relationship(
        back_populates="topic", passive_deletes=True
    )