"""Business logic for persisted learning-resource selections.

All database operations, ownership filtering, URL normalization and
duplicate prevention live here. Routes stay thin: translate HTTP into
service calls and map service errors to HTTP errors.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import LearningResourceSelection, Subject
from app.schemas.learning_resources import (
    SelectLearningResourceRequest,
    LearningResourceSelectionResponse,
    ResourceType,
)
from app.services.learning_resources.quality import canonical_resource_url


class SelectionError(Exception):
    """Base class for selection service errors."""


class SelectionNotFoundError(SelectionError):
    """Raised when a selection is missing or owned by someone else."""


class DuplicateSelectionError(SelectionError):
    """Raised when the same URL is already selected by this user."""


class InvalidResourceUrlError(SelectionError):
    """Raised when the supplied URL cannot be normalized to http/https."""


class SubjectNotFoundError(SelectionError):
    """Raised when the referenced subject is missing or owned by someone else."""


def _domain_from_url(url: str) -> str:
    """Extract the normalized domain from a canonical URL ("" if none)."""
    from app.services.learning_resources.classifier import extract_domain

    return extract_domain(url)


def to_response(selection: LearningResourceSelection) -> LearningResourceSelectionResponse:
    return LearningResourceSelectionResponse(
        id=selection.id,
        subject_id=selection.subject_id,
        title=selection.title,
        url=selection.url,
        domain=selection.domain,
        resource_type=ResourceType(selection.resource_type),
        is_official=selection.is_official,
        difficulty=selection.difficulty,
        description=selection.description or "",
        source=selection.source,
        created_at=selection.created_at,
        last_used_at=selection.last_used_at,
    )


def create_selection(
    db: Session,
    user_id: uuid.UUID,
    data: SelectLearningResourceRequest,
) -> LearningResourceSelection:
    """Persist a web-resource selection for the user.

    The URL is canonicalized before storage; selecting the same URL twice
    is prevented both here and by the database unique constraint.
    """
    url = canonical_resource_url(data.url)
    if not url:
        raise InvalidResourceUrlError(
            "URL must be a valid http(s) URL without embedded credentials"
        )

    if data.subject_id is not None:
        subject = (
            db.query(Subject)
            .filter(Subject.id == data.subject_id, Subject.owner_id == user_id)
            .first()
        )
        if subject is None:
            raise SubjectNotFoundError

    selection = LearningResourceSelection(
        user_id=user_id,
        subject_id=data.subject_id,
        title=data.title,
        url=url,
        domain=data.domain.strip() or _domain_from_url(url),
        resource_type=data.resource_type.value,
        is_official=data.is_official,
        difficulty=data.difficulty,
        description=data.description.strip() or None,
        source=data.source.strip() or "web_search",
    )
    db.add(selection)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateSelectionError
    db.refresh(selection)
    return selection


def list_selections(
    db: Session,
    user_id: uuid.UUID,
    *,
    subject_id: uuid.UUID | None = None,
    limit: int = 100,
) -> list[LearningResourceSelection]:
    """List the user's selections, newest first (deterministic tie-break)."""
    query = db.query(LearningResourceSelection).filter(
        LearningResourceSelection.user_id == user_id
    )
    if subject_id is not None:
        query = query.filter(LearningResourceSelection.subject_id == subject_id)
    return (
        query.order_by(
            LearningResourceSelection.created_at.desc(),
            LearningResourceSelection.id.desc(),
        )
        .limit(max(1, min(limit, 200)))
        .all()
    )


def get_selection(
    db: Session,
    selection_id: uuid.UUID,
    user_id: uuid.UUID,
) -> LearningResourceSelection:
    """Return one selection if it exists AND belongs to the user."""
    selection = (
        db.query(LearningResourceSelection)
        .filter(
            LearningResourceSelection.id == selection_id,
            LearningResourceSelection.user_id == user_id,
        )
        .first()
    )
    if selection is None:
        raise SelectionNotFoundError
    return selection


def delete_selection(
    db: Session,
    selection_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Delete a selection owned by the user."""
    selection = get_selection(db, selection_id, user_id)
    db.delete(selection)
    db.commit()


def mark_selections_used(
    db: Session,
    selections: list[LearningResourceSelection],
) -> None:
    """Record when selections were last included in an AI context."""
    if not selections:
        return
    now = datetime.now(timezone.utc)
    for selection in selections:
        selection.last_used_at = now
    db.commit()