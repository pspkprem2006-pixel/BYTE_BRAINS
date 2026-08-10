"""Business logic for Material upload and text extraction."""

import os
import uuid
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.models import Material, Subject, ProcessingStatus
from app.schemas.material import MaterialCreate


UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
}


class MaterialError(Exception):
    """Base class for material service errors."""


class InvalidFileTypeError(MaterialError):
    """Raised when uploaded file type is not supported."""


class FileTooLargeError(MaterialError):
    """Raised when uploaded file exceeds size limit."""


class SubjectNotFoundError(MaterialError):
    """Raised when subject is missing or owned by someone else."""


class EmptyDocumentError(MaterialError):
    """Raised when document has no extractable text."""


class ExtractionError(MaterialError):
    """Raised when text extraction fails."""


def _generate_safe_filename(original: str, file_type: str) -> str:
    """Generate a safe stored filename."""
    ext = ALLOWED_TYPES.get(file_type, "")
    unique_id = uuid.uuid4().hex[:12]
    return f"{unique_id}{ext}"


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _save_upload(file: BinaryIO, filename: str) -> Path:
    _ensure_upload_dir()
    dest = UPLOAD_DIR / filename
    with dest.open("wb") as out:
        while chunk := file.read(8192):
            out.write(chunk)
    return dest


def _extract_text(path: Path, file_type: str) -> str:
    """Extract text from saved file."""
    if file_type == "text/plain":
        return path.read_text(encoding="utf-8", errors="replace")

    if file_type == "application/pdf":
        try:
            reader = PdfReader(str(path))
            texts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    texts.append(text)
            return "\n\n".join(texts)
        except Exception as e:
            raise ExtractionError(f"PDF extraction failed: {e}") from e

    raise InvalidFileTypeError(f"Unsupported file type: {file_type}")


def create_material(
    db: Session,
    user_id: uuid.UUID,
    subject_id: uuid.UUID,
    file: BinaryIO,
    filename: str,
    file_type: str,
    file_size: int,
) -> Material:
    """Upload a file, extract text, and create a Material record."""
    if file_type not in ALLOWED_TYPES:
        raise InvalidFileTypeError("Only PDF and TXT files are supported.")

    if file_size > MAX_FILE_SIZE:
        raise FileTooLargeError("File size exceeds 10 MB limit.")

    # Verify subject belongs to user
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.owner_id == user_id)
        .first()
    )
    if subject is None:
        raise SubjectNotFoundError

    safe_name = _generate_safe_filename(filename, file_type)
    saved_path = _save_upload(file, safe_name)

    try:
        extracted = _extract_text(saved_path, file_type)
    except ExtractionError:
        saved_path.unlink(missing_ok=True)
        raise
    except Exception as e:
        saved_path.unlink(missing_ok=True)
        raise ExtractionError(f"Extraction failed: {e}") from e

    if not extracted or not extracted.strip():
        saved_path.unlink(missing_ok=True)
        raise EmptyDocumentError("No extractable text found. Scanned/image-only PDFs are not supported.")

    material = Material(
        user_id=user_id,
        subject_id=subject_id,
        filename=safe_name,
        original_filename=filename,
        file_type=file_type,
        file_size=file_size,
        storage_path=str(saved_path),
        processing_status=ProcessingStatus.processed,
        extracted_text=extracted.strip(),
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def list_materials(
    db: Session, user_id: uuid.UUID, subject_id: uuid.UUID | None = None
) -> list[Material]:
    """Return materials for the user, optionally filtered by subject."""
    query = db.query(Material).filter(Material.user_id == user_id)
    if subject_id:
        query = query.filter(Material.subject_id == subject_id)
    return query.order_by(Material.created_at.desc()).all()