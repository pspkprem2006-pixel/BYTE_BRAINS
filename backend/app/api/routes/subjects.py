"""Subject REST API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Subject, User
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services import subject_service
from app.services.development_user import get_current_development_user

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user.

    TEMPORARY: uses the development user. Replaced by real authentication
    (``get_current_user`` with a token) during the authentication phase —
    the rest of the code base does not need to change.
    """
    return get_current_development_user(db)


@router.get(
    "",
    response_model=list[SubjectResponse],
    summary="List subjects",
    description="Return every subject owned by the current user.",
)
def list_subjects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Subject]:
    return subject_service.list_subjects(db, user.id)


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Get one subject",
    description="Return a single subject if it belongs to the current user.",
)
def get_subject(
    subject_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Subject:
    try:
        return subject_service.get_subject(db, subject_id, user.id)
    except subject_service.SubjectNotFoundError:
        raise HTTPException(status_code=404, detail="Subject not found")


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a subject",
    description="Create a new subject owned by the current user.",
)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Subject:
    try:
        return subject_service.create_subject(db, user.id, payload)
    except subject_service.DuplicateSubjectError:
        raise HTTPException(
            status_code=409, detail="A subject with this name already exists"
        )


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Update a subject",
    description="Update one subject. Any field left out stays unchanged.",
)
def update_subject(
    subject_id: uuid.UUID,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Subject:
    try:
        return subject_service.update_subject(db, subject_id, user.id, payload)
    except subject_service.SubjectNotFoundError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except subject_service.DuplicateSubjectError:
        raise HTTPException(
            status_code=409, detail="A subject with this name already exists"
        )


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a subject",
    description="Delete a subject owned by the current user.",
)
def delete_subject(
    subject_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    try:
        subject_service.delete_subject(db, subject_id, user.id)
    except subject_service.SubjectNotFoundError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except subject_service.SubjectDeleteConflictError:
        raise HTTPException(
            status_code=409,
            detail="Subject cannot be deleted because quiz attempts reference it",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)