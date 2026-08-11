"""Progress REST API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.progress import ProgressItem
from app.services import quiz_progress_service
from app.services.development_user import get_current_development_user

router = APIRouter(prefix="/api/progress", tags=["progress"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user (development user for now)."""
    return get_current_development_user(db)


@router.get(
    "",
    response_model=list[ProgressItem],
    summary="List topic mastery",
    description="Return the current user's per-topic mastery built from quiz results.",
)
def get_progress(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProgressItem]:
    rows = quiz_progress_service.get_user_progress(db, user)
    return [
        ProgressItem(
            topic_id=progress.topic_id,
            topic_name=topic_name,
            subject_id=progress.topic.subject_id,
            subject_name=subject_name,
            mastery_score=progress.mastery_score,
            topics_completed=progress.topics_completed,
            last_studied_at=progress.last_studied_at,
        )
        for progress, topic_name, subject_name in rows
    ]
