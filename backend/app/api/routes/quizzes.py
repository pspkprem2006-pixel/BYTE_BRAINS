"""Quiz REST API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Material, Subject, User
from app.schemas.quiz import (
    QuizAttemptSummary,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services import (
    ai_service,
    quiz_progress_service,
    resource_selection_service,
)
from app.services.development_user import get_current_development_user
from app.services.learning_context_service import LearningContextService

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user (development user for now)."""
    return get_current_development_user(db)


@router.post(
    "/generate",
    response_model=QuizGenerateResponse,
    summary="Generate a quiz from material and/or web resources",
    description="Ask the AI to create multiple-choice questions based on uploaded material and/or selected web resources.",
)
async def generate_quiz(
    request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> QuizGenerateResponse:
    material: Material | None = None
    if request.material_id is not None:
        material = (
            db.query(Material)
            .filter(Material.id == request.material_id, Material.user_id == user.id)
            .first()
        )
        if material is None:
            raise HTTPException(status_code=404, detail="Material not found")

    subject: Subject | None = None
    if request.subject_id is not None:
        subject = (
            db.query(Subject)
            .filter(Subject.id == request.subject_id, Subject.owner_id == user.id)
            .first()
        )
        if subject is None:
            raise HTTPException(status_code=404, detail="Subject not found")

    if subject is None and material is not None and material.subject_id is not None:
        subject = (
            db.query(Subject)
            .filter(Subject.id == material.subject_id, Subject.owner_id == user.id)
            .first()
        )

    has_web_resources = False
    if subject is not None:
        has_web_resources = (
            resource_selection_service.list_selections(
                db,
                user.id,
                subject_id=subject.id,
                limit=1,
            )
            != []
        )

    material_has_text = bool(
        material is not None
        and material.extracted_text
        and material.extracted_text.strip()
    )

    # LEGACY MODE: material with text and no web selections -> existing path.
    if material is not None and material_has_text and not has_web_resources:
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

    # CONTEXT MODE: combine uploaded material and/or web resources.
    context = LearningContextService().build_context(
        db,
        user.id,
        material=material,
        subject=subject,
        question="",
    )

    if context.is_empty:
        if material is not None:
            raise HTTPException(
                status_code=422,
                detail="Material has no extracted text to generate a quiz from.",
            )
        raise HTTPException(
            status_code=422,
            detail=(
                "No learning context available to generate a quiz from. "
                "Find learning resources for this subject first."
            ),
        )

    try:
        quiz = await ai_service.generate_quiz_from_context(
            request.question_count,
            context.render(),
            subject_name=context.subject_name,
            material_id=material.id if material is not None else None,
        )
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

    if subject is not None:
        quiz.subject_id = subject.id
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
    except quiz_progress_service.SubjectNotFoundError:
        raise HTTPException(status_code=404, detail="Subject not found")

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