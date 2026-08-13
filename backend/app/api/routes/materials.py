"""Material REST API routes."""

import uuid
from io import BytesIO

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.material import MaterialResponse
from app.services import material_service
from app.services.development_user import get_current_development_user

router = APIRouter(prefix="/api/materials", tags=["materials"])


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user (development user for now)."""
    return get_current_development_user(db)


@router.post(
    "/upload",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload study material",
    description="Upload a PDF or TXT file, extract text, and store metadata.",
)
async def upload_material(
    subject_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MaterialResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    # Read only up to the size limit: anything larger is rejected before the
    # whole payload is held in memory.
    content = await file.read(material_service.MAX_FILE_SIZE + 1)
    file_size = len(content)
    if file_size > material_service.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit.")

    try:
        material = material_service.create_material(
            db=db,
            user_id=user.id,
            subject_id=subject_id,
            file=BytesIO(content),
            filename=file.filename,
            file_type=file.content_type or "application/octet-stream",
            file_size=file_size,
        )
    except material_service.InvalidFileTypeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except material_service.FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except material_service.SubjectNotFoundError:
        raise HTTPException(status_code=404, detail="Subject not found")
    except material_service.EmptyDocumentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except material_service.ExtractionError:
        raise HTTPException(
            status_code=422,
            detail="Could not read the file. Make sure the PDF is valid and text-based.",
        )

    return material


@router.get(
    "",
    response_model=list[MaterialResponse],
    summary="List materials",
    description="Return materials for the current user, optionally filtered by subject.",
)
def list_materials(
    subject_id: uuid.UUID | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MaterialResponse]:
    return material_service.list_materials(db, user.id, subject_id)