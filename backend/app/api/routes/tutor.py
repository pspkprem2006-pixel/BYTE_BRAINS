"""Tutor REST API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Material, User
from app.schemas.tutor import TutorAskRequest, TutorAskResponse
from app.services import ai_service
from app.services.development_user import get_current_development_user

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user (development user for now)."""
    return get_current_development_user(db)


@router.post(
    "/ask",
    response_model=TutorAskResponse,
    summary="Ask the AI Tutor",
    description="Ask a question about uploaded study material.",
)
async def ask_tutor(
    request: TutorAskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TutorAskResponse:
    # Verify material belongs to user
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

    if not material.extracted_text or not material.extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Material has no extracted text to answer from.",
        )

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