"""Persist quiz attempts and per-topic mastery.

Quiz results are the source of truth for progress: every submitted attempt
creates a ``QuizAttempt`` row, and each topic in the attempt updates the
user's ``UserProgress`` row (one row per user/topic, upserted so repeated
quizzes improve mastery instead of duplicating rows).

Topic rows are created on demand under the material's subject, since AI
generated topics may not exist yet.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import Material, QuizAttempt, Subject, Topic, User, UserProgress
from app.schemas.quiz import QuizSubmitRequest


class MaterialNotFoundError(Exception):
    """Raised when the material is missing or owned by another user."""


def _score_percent(correct: int, total: int) -> int:
    return round(correct / total * 100)


def submit_quiz_attempt(
    db: Session, user: User, request: QuizSubmitRequest
) -> QuizAttempt:
    """Create a quiz attempt row and upsert per-topic mastery."""
    material = (
        db.query(Material)
        .filter(Material.id == request.material_id, Material.user_id == user.id)
        .first()
    )
    if material is None:
        raise MaterialNotFoundError

    now = datetime.now(timezone.utc)
    attempt = QuizAttempt(
        user_id=user.id,
        subject_id=material.subject_id,
        quiz_title=f"Quiz: {material.original_filename}",
        total_questions=request.total_questions,
        correct_answers=request.correct_answers,
        score=_score_percent(request.correct_answers, request.total_questions),
        completed_at=now,
    )
    db.add(attempt)

    for result in request.topic_results:
        topic = (
            db.query(Topic)
            .filter(
                Topic.subject_id == material.subject_id,
                Topic.name == result.topic,
            )
            .first()
        )
        if topic is None:
            topic = Topic(subject_id=material.subject_id, name=result.topic)
            db.add(topic)
            db.flush()

        progress = (
            db.query(UserProgress)
            .filter(
                UserProgress.user_id == user.id,
                UserProgress.topic_id == topic.id,
            )
            .first()
        )
        topic_score = _score_percent(result.correct, result.total)
        if progress is None:
            progress = UserProgress(
                user_id=user.id,
                topic_id=topic.id,
                mastery_score=topic_score,
                topics_completed=1,
                last_studied_at=now,
            )
            db.add(progress)
        else:
            completed = progress.topics_completed
            progress.mastery_score = round(
                (progress.mastery_score * completed + topic_score)
                / (completed + 1)
            )
            progress.topics_completed = completed + 1
            progress.last_studied_at = now

    db.commit()
    db.refresh(attempt)
    return attempt


def list_recent_attempts(
    db: Session, user: User, limit: int = 10
) -> list[tuple[QuizAttempt, str]]:
    """Return the user's most recent attempts with their subject names."""
    return (
        db.query(QuizAttempt, Subject.name)
        .join(Subject, Subject.id == QuizAttempt.subject_id)
        .filter(QuizAttempt.user_id == user.id)
        .order_by(desc(QuizAttempt.completed_at), QuizAttempt.id)
        .limit(limit)
        .all()
    )


def get_user_progress(
    db: Session, user: User
) -> list[tuple[UserProgress, str, str]]:
    """Return (progress, topic_name, subject_name) rows for the user."""
    return (
        db.query(UserProgress, Topic.name, Subject.name)
        .join(Topic, Topic.id == UserProgress.topic_id)
        .join(Subject, Subject.id == Topic.subject_id)
        .filter(UserProgress.user_id == user.id)
        .order_by(desc(UserProgress.last_studied_at), UserProgress.topic_id)
        .all()
    )
