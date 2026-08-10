"""Business logic for the Topic API.

Topics always live inside a subject, so every operation first verifies
that the subject exists AND belongs to the current user (via the shared
subject service), then scopes all queries to that subject.
"""

import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Subject, Topic
from app.schemas.topic import TopicCreate, TopicUpdate
from app.services.subject_service import SubjectNotFoundError, get_subject


class TopicError(Exception):
    """Base class for topic service errors."""


class TopicNotFoundError(TopicError):
    """Raised when a topic is missing or does not belong to the subject."""


class SubjectAccessError(TopicError):
    """Raised when the subject is missing or owned by someone else."""


def _require_subject(db: Session, subject_id: uuid.UUID, user_id: uuid.UUID) -> Subject:
    """Return the subject if the user owns it, otherwise raise."""
    try:
        return get_subject(db, subject_id, user_id)
    except SubjectNotFoundError:
        raise SubjectAccessError


def list_topics(
    db: Session, subject_id: uuid.UUID, user_id: uuid.UUID
) -> list[Topic]:
    """Return every topic of the given subject, in display order."""
    _require_subject(db, subject_id, user_id)
    return (
        db.query(Topic)
        .filter(Topic.subject_id == subject_id)
        .order_by(Topic.order_index, Topic.name)
        .all()
    )


def get_topic(
    db: Session, subject_id: uuid.UUID, topic_id: uuid.UUID, user_id: uuid.UUID
) -> Topic:
    """Return one topic if it belongs to the given subject of the user.

    Uses an inner join on ``subjects``, so a topic whose subject is
    missing or owned by someone else is indistinguishable from a topic
    that does not exist at all.
    """
    topic = (
        db.query(Topic)
        .join(Subject)
        .filter(
            Topic.id == topic_id,
            Topic.subject_id == subject_id,
            Subject.owner_id == user_id,
        )
        .first()
    )
    if topic is None:
        raise TopicNotFoundError
    return topic


def create_topic(
    db: Session, subject_id: uuid.UUID, user_id: uuid.UUID, data: TopicCreate
) -> Topic:
    """Create a topic inside the given subject."""
    _require_subject(db, subject_id, user_id)

    if data.order_index is None:
        last_index = (
            db.query(func.max(Topic.order_index))
            .filter(Topic.subject_id == subject_id)
            .scalar()
        )
        order_index = (last_index if last_index is not None else -1) + 1
    else:
        order_index = data.order_index

    topic = Topic(
        subject_id=subject_id,
        name=data.name,
        description=data.description,
        order_index=order_index,
    )
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def update_topic(
    db: Session,
    subject_id: uuid.UUID,
    topic_id: uuid.UUID,
    user_id: uuid.UUID,
    data: TopicUpdate,
) -> Topic:
    """Update an existing topic (partial updates supported)."""
    topic = get_topic(db, subject_id, topic_id, user_id)

    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(topic, field, value)

    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(
    db: Session, subject_id: uuid.UUID, topic_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Delete a topic of the given subject."""
    topic = get_topic(db, subject_id, topic_id, user_id)
    db.delete(topic)
    db.commit()