"""Tutor REST API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Material, Subject, User
from app.schemas.tutor import TutorAskRequest, TutorAskResponse
from app.services import ai_service, resource_selection_service
from app.services.development_user import get_current_development_user
from app.services.learning_context_service import LearningContextService

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user (development user for now)."""
    return get_current_development_user(db)


@router.post(
    "/ask",
    response_model=TutorAskResponse,
    summary="Ask the AI Tutor",
    description="Ask a question about uploaded study material and/or selected web resources.",
)
async def ask_tutor(
    request: TutorAskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TutorAskResponse:
    material: Material | None = None
    if request.material_id is not None:
        material = (
            db.query(Material)
            .filter(Material.id == request.material_id, Material.user_id == user.id)
            .first()
        )
        if material is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Material not found",
            )

    subject: Subject | None = None
    if request.subject_id is not None:
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

    # When only a material is given (and the request did not explicitly
    # target a subject), derive the subject from the material so its web
    # resources can be included when they exist.
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
            answer = await ai_service.ask_tutor(material, request.question)
        except ai_service.MissingAPIKeyError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Tutor is not configured. Please contact the administrator.",
            )
        except ai_service.EmptyMaterialError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Material has no extracted text.",
            )
        except ai_service.AIServiceError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI Tutor is temporarily unavailable. Please try again.",
            )

        return TutorAskResponse(
            material_id=material.id,
            question=request.question,
            answer=answer,
        )

    # CONTEXT MODE: combine uploaded material and/or web resources.
    context = LearningContextService().build_context(
        db,
        user.id,
        material=material,
        subject=subject,
        question=request.question,
    )

    if context.is_empty:
        if material is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Material has no extracted text to answer from.",
            )
        return TutorAskResponse(
            material_id=None,
            question=request.question,
            answer=(
                "I don't have any learning content yet. Find learning "
                "resources for this subject (or upload study material), "
                "then ask me again."
            ),
        )

    try:
        answer = await ai_service.ask_tutor_with_learning_context(
            request.question,
            context.render(),
            subject_name=context.subject_name,
        )
    except ai_service.MissingAPIKeyError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Tutor is not configured. Please contact the administrator.",
        )
    except ai_service.EmptyMaterialError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Material has no extracted text to answer from.",
        )
    except ai_service.AIServiceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI Tutor is temporarily unavailable. Please try again.",
        )

    return TutorAskResponse(
        material_id=material.id if material is not None else None,
        question=request.question,
        answer=answer,
    )
