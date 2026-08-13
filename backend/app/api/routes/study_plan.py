"""Study Plan REST API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Material, Subject, User
from app.schemas.study_plan import (
    StudyPlanGenerateRequest,
    StudyPlanGenerateResponse,
)
from app.services import ai_service, resource_selection_service
from app.services.development_user import get_current_development_user
from app.services.learning_context_service import LearningContextService

router = APIRouter(prefix="/api/study-plan", tags=["study-plan"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user (development user for now)."""
    return get_current_development_user(db)


@router.post(
    "/generate",
    response_model=StudyPlanGenerateResponse,
    summary="Generate a personalized AI study plan",
    description="Create a day-by-day study plan based on the subject, available time, weak topics, and material context.",
)
async def generate_study_plan(
    request: StudyPlanGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudyPlanGenerateResponse:
    subject = (
        db.query(Subject)
        .filter(Subject.id == request.subject_id, Subject.owner_id == user.id)
        .first()
    )

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    # Gather material context for the subject using the existing lightweight retrieval.
    materials = (
        db.query(Material)
        .filter(Material.subject_id == subject.id, Material.user_id == user.id)
        .all()
    )
    material_context = ""
    if materials:
        text_parts = [
            m.extracted_text for m in materials if m.extracted_text and m.extracted_text.strip()
        ]
        if text_parts:
            combined = "\n\n".join(text_parts)
            material_context = ai_service._retrieve_relevant_chunks(
                combined, "key concepts summary"
            )

    # Include the subject's selected web resources (metadata only).
    web_resource_context, web_selections = LearningContextService().build_web_resource_context(
        db,
        user.id,
        subject_id=subject.id,
    )
    if web_selections:
        resource_selection_service.mark_selections_used(db, web_selections)

    try:
        plan = await ai_service.generate_study_plan(
            subject_id=subject.id,
            subject_name=subject.name,
            material_context=material_context,
            web_resource_context=web_resource_context,
            days_available=request.days_available,
            hours_per_day=request.hours_per_day,
            focus=request.focus.value,
            exam_date=request.exam_date,
            weak_topics=request.weak_topics,
        )
    except ai_service.MissingAPIKeyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Study Plan is not configured. Please contact the administrator.",
        )
    except ai_service.StudyPlanGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except ai_service.AIServiceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Study Plan is temporarily unavailable. Please try again.",
        )

    return plan