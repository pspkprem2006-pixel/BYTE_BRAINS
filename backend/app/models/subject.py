"""Subject model."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Subject(UUIDMixin, TimestampMixin, Base):
    """A study subject owned by one user (e.g. DBMS, Python)."""

    __tablename__ = "subjects"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    owner: Mapped["User"] = relationship(back_populates="subjects")

    topics: Mapped[list["Topic"]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
        order_by="Topic.order_index",
    )
    # Materials keep existing (user data) when a subject is deleted:
    # their subject link is set to NULL instead.
    materials: Mapped[list["Material"]] = relationship(
        back_populates="subject", passive_deletes=True
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="subject"
    )