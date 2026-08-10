"""User model."""

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TimestampMixin, UUIDMixin
from app.core.database import Base


class User(UUIDMixin, TimestampMixin, Base):
    """A student using ByteBrains.

    Authentication fields (password, etc.) arrive in a later phase.
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    materials: Mapped[list["Material"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    progress: Mapped[list["UserProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    study_plans: Mapped[list["StudyPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )