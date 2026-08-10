"""Material model."""

import enum
import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class ProcessingStatus(str, enum.Enum):
    """Lifecycle of an uploaded study document."""

    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class Material(UUIDMixin, TimestampMixin, Base):
    """Metadata record for an uploaded study document."""

    __tablename__ = "materials"
    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('uploaded', 'processing', 'processed', 'failed')",
            name="ck_materials_processing_status",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    processing_status: Mapped[str] = mapped_column(
        String(20),
        default=ProcessingStatus.uploaded,
        nullable=False,
    )
    # Extracted text content for AI Tutor (nullable until processing completes)
    extracted_text: Mapped[str | None] = mapped_column(Text)

    owner: Mapped["User"] = relationship(back_populates="materials")
    subject: Mapped["Subject | None"] = relationship(back_populates="materials")