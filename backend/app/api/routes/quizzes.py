"""Quiz REST API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Material, User
from app.schemas.quiz import (
    QuizAttemptSummary,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services import ai_service, quiz_progress_service
from app.services.development_user import get_current_development_user

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user (development user for now)."""
    return get_current_development_user(db)


@router.post(
    "/generate",
    response_model=QuizGenerateResponse,
    summary="Generate a quiz from material",
    description="Ask the AI to create multiple-choice questions based on uploaded material.",
)
async def generate_quiz(
    request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuizGenerateResponse:
    material = (
        db.query(Material)
        .filter(Material.id == request.material_id, Material.user_id == user.id)
        .first()
    )

    if material is None:
        raise HTTPException(status_code=404, detail="Material not found")

    if not material.extracted_text or not material.extracted_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Material has no extracted text to generate a quiz from.",
        )

    try:
        quiz = await ai_service.generate_quiz(material, request.question_count)
    except ai_service.MissingAPIKeyError:
        raise HTTPException(
            status_code=503,
            detail="AI Quiz is not configured. Please contact the administrator.",
        )
    except ai_service.EmptyMaterialError:
        raise HTTPException(
            status_code=422,
            detail="Material has no extracted text.",
        )
    except ai_service.QuizGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ai_service.AIServiceError:
        raise HTTPException(
            status_code=503,
            detail="AI Quiz is temporarily unavailable. Please try again.",
        )

    return quiz


@router.post(
    "/submit",
    response_model=QuizSubmitResponse,
    summary="Persist a finished quiz attempt",
    description="Save the outcome of a completed quiz and update per-topic mastery.",
)
def submit_quiz_attempt(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuizSubmitResponse:
    try:
        attempt = quiz_progress_service.submit_quiz_attempt(db, user, request)
    except quiz_progress_service.MaterialNotFoundError:
        raise HTTPException(status_code=404, detail="Material not found")

    return QuizSubmitResponse(
        attempt_id=attempt.id,
        quiz_title=attempt.quiz_title,
        total_questions=attempt.total_questions,
        correct_answers=attempt.correct_answers,
        score=attempt.score,
        completed_at=attempt.completed_at,
    )


@router.get(
    "/attempts",
    response_model=list[QuizAttemptSummary],
    summary="List recent quiz attempts",
    description="Return the current user's most recent quiz attempts.",
)
def list_quiz_attempts(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[QuizAttemptSummary]:
    rows = quiz_progress_service.list_recent_attempts(db, user, limit)
    return [
        QuizAttemptSummary(
            id=attempt.id,
            quiz_title=attempt.quiz_title,
            subject_id=attempt.subject_id,
            subject_name=subject_name,
            total_questions=attempt.total_questions,
            correct_answers=attempt.correct_answers,
            score=attempt.score,
            completed_at=attempt.completed_at,
        )
        for attempt, subject_name in rows
    ]