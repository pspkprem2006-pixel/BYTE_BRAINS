"""Topic REST API routes.

Topics are always nested inside a subject:
``/api/subjects/{subject_id}/topics[/{topic_id}]``.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Topic, User
from app.schemas.topic import TopicCreate, TopicResponse, TopicUpdate
from app.services import topic_service
from app.services.development_user import get_current_development_user

router = APIRouter(
    prefix="/api/subjects/{subject_id}/topics", tags=["topics"]
)


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user.

    TEMPORARY: uses the development user. Replaced by real authentication
    (``get_current_user`` with a token) during the authentication phase —
    the rest of the code base does not need to change.
    """
    return get_current_development_user(db)


@router.get(
    "",
    response_model=list[TopicResponse],
    summary="List topics",
    description="Return every topic of the given subject, in display order.",
)
def list_topics(
    subject_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Topic]:
    try:
        return topic_service.list_topics(db, subject_id, user.id)
    except topic_service.SubjectAccessError:
        raise HTTPException(status_code=404, detail="Subject not found")


@router.get(
    "/{topic_id}",
    response_model=TopicResponse,
    summary="Get one topic",
    description="Return a single topic of the given subject.",
)
def get_topic(
    subject_id: uuid.UUID,
    topic_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Topic:
    try:
        return topic_service.get_topic(db, subject_id, topic_id, user.id)
    except topic_service.TopicNotFoundError:
        raise HTTPException(status_code=404, detail="Topic not found")


@router.post(
    "",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a topic",
    description="Create a new topic inside the given subject.",
)
def create_topic(
    subject_id: uuid.UUID,
    payload: TopicCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Topic:
    try:
        return topic_service.create_topic(db, subject_id, user.id, payload)
    except topic_service.SubjectAccessError:
        raise HTTPException(status_code=404, detail="Subject not found")


@router.put(
    "/{topic_id}",
    response_model=TopicResponse,
    summary="Update a topic",
    description="Update one topic. Any field left out stays unchanged.",
)
def update_topic(
    subject_id: uuid.UUID,
    topic_id: uuid.UUID,
    payload: TopicUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Topic:
    try:
        return topic_service.update_topic(db, subject_id, topic_id, user.id, payload)
    except topic_service.TopicNotFoundError:
        raise HTTPException(status_code=404, detail="Topic not found")


@router.delete(
    "/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a topic",
    description="Delete a topic of the given subject.",
)
def delete_topic(
    subject_id: uuid.UUID,
    topic_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    try:
        topic_service.delete_topic(db, subject_id, topic_id, user.id)
    except topic_service.TopicNotFoundError:
        raise HTTPException(status_code=404, detail="Topic not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)