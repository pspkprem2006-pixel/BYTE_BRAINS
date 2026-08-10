"""QuizAttempt model."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin


class QuizAttempt(UUIDMixin, Base):
    """A finished quiz attempt by a user.

    The quiz engine arrives in a later phase; this model only stores
    the outcome of an attempt.
    """

    __tablename__ = "quiz_attempts"
    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100", name="ck_quiz_attempts_score_range"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"), nullable=False
    )
    # Optional: an attempt may target a specific topic.
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), index=True
    )
    quiz_title: Mapped[str] = mapped_column(String(200), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, nullable=False)
    # Score as a percentage, 0-100 (matches the frontend's "Score: X%").
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="quiz_attempts")
    subject: Mapped["Subject"] = relationship(back_populates="quiz_attempts")
    topic: Mapped["Topic | None"] = relationship(back_populates="quiz_attempts")