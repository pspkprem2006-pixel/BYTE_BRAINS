"""Business logic for the Subject API.

The service layer owns all database operations, ownership filtering and
business rules. Route handlers stay thin: they only translate HTTP into
service calls and map service errors to HTTP errors.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


class SubjectError(Exception):
    """Base class for subject service errors."""


class SubjectNotFoundError(SubjectError):
    """Raised when a subject is missing or owned by someone else."""


class DuplicateSubjectError(SubjectError):
    """Raised when a subject name already exists."""


class SubjectDeleteConflictError(SubjectError):
    """Raised when a subject cannot be deleted due to database constraints."""


def list_subjects(db: Session, user_id: uuid.UUID) -> list[Subject]:
    """Return all subjects owned by the given user, ordered by name."""
    return (
        db.query(Subject)
        .filter(Subject.owner_id == user_id)
        .order_by(Subject.name)
        .all()
    )


def get_subject(db: Session, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject:
    """Return one subject if it exists AND belongs to the user."""
    subject = (
        db.query(Subject)
        .filter(Subject.id == subject_id, Subject.owner_id == user_id)
        .first()
    )
    if subject is None:
        raise SubjectNotFoundError
    return subject


def create_subject(
    db: Session, user_id: uuid.UUID, data: SubjectCreate
) -> Subject:
    """Create a subject owned by the given user."""
    subject = Subject(
        owner_id=user_id,
        name=data.name,
        description=data.description,
    )
    db.add(subject)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateSubjectError
    db.refresh(subject)
    return subject


def update_subject(
    db: Session, subject_id: uuid.UUID, user_id: uuid.UUID, data: SubjectUpdate
) -> Subject:
    """Update an existing subject (partial updates supported)."""
    subject = get_subject(db, subject_id, user_id)

    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(subject, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateSubjectError
    db.refresh(subject)
    return subject


def delete_subject(db: Session, subject_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Delete a subject owned by the given user."""
    subject = get_subject(db, subject_id, user_id)

    db.delete(subject)
    try:
        db.commit()
    except IntegrityError:
        # e.g. quiz_attempts has a RESTRICT foreign key pointing at this
        # subject, so PostgreSQL refuses the deletion.
        db.rollback()
        raise SubjectDeleteConflictError