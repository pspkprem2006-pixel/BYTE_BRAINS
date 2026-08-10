"""Material model."""

import enum
import uuid

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String
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
    """Metadata record for an uploaded study document.

    The actual file upload and processing arrive in later phases;
    these fields only describe the file for now.
    """

    __tablename__ = "materials"
    __table_args__ = (
        # Values are constrained by the database via a CHECK constraint
        # (the Python ProcessingStatus enum validates on the API side).
        CheckConstraint(
            "processing_status IN ('uploaded', 'processing', 'processed', 'failed')",
            name="ck_materials_processing_status",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # Optional: a material may or may not belong to a subject.
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    # Location of the stored file (metadata only for now).
    storage_path: Mapped[str | None] = mapped_column(String(500))
    processing_status: Mapped[str] = mapped_column(
        String(20),
        default=ProcessingStatus.uploaded,
        nullable=False,
    )

    owner: Mapped["User"] = relationship(back_populates="materials")
    subject: Mapped["Subject | None"] = relationship(back_populates="materials")