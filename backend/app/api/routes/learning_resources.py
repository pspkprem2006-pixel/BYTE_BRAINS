"""Learning Resources REST API routes.

Discovery endpoint for web learning resources (POST + GET) and persistence
endpoints for the user's selected resources (select / list / delete). All
go through the same validation and service layers. Search results are
treated as untrusted text: they are never rendered as HTML server-side and
never passed to an AI system here.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from app.core.database import get_db
from app.models import User
from app.schemas.learning_resources import (
    QUERY_MAX_LENGTH,
    RESOURCE_COUNT_MAX,
    LearningResourceRequest,
    LearningResourcesResponse,
    SelectLearningResourceRequest,
    LearningResourceSelectionResponse,
    SelectedResourcesResponse,
)
from app.services import resource_selection_service
from app.services.development_user import get_current_development_user
from app.services.learning_resources.service import LearningResourceService
from app.services.search.errors import (
    InvalidSearchQueryError,
    WebSearchError,
    WebSearchNotConfiguredError,
    WebSearchTimeoutError,
)
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/learning-resources", tags=["learning-resources"])


def get_learning_resource_service() -> LearningResourceService:
    """FastAPI dependency: a fresh discovery service per request."""
    return LearningResourceService()


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Resolve the acting user (development user for now)."""
    return get_current_development_user(db)


async def _run_discovery(
    request: LearningResourceRequest,
    service: LearningResourceService,
) -> LearningResourcesResponse:
    try:
        resources = await service.discover(request)
    except WebSearchNotConfiguredError:
        raise HTTPException(
            status_code=503,
            detail="Web search is not configured. Please contact the administrator.",
        )
    except WebSearchTimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Web search timed out. Please try again.",
        )
    except InvalidSearchQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except WebSearchError:
        raise HTTPException(
            status_code=503,
            detail="Unable to search the web right now. Please try again.",
        )
    return LearningResourcesResponse(query=request.query, resources=resources)


@router.post("", response_model=LearningResourcesResponse)
async def discover_learning_resources(
    request: LearningResourceRequest,
    service: LearningResourceService = Depends(get_learning_resource_service),
) -> LearningResourcesResponse:
    """Discover curated learning resources for a topic."""
    return await _run_discovery(request, service)


@router.get("", response_model=LearningResourcesResponse)
async def discover_learning_resources_get(
    query: str = Query(default="", max_length=QUERY_MAX_LENGTH),
    count: int | None = Query(default=None, ge=1, le=RESOURCE_COUNT_MAX),
    service: LearningResourceService = Depends(get_learning_resource_service),
) -> LearningResourcesResponse:
    """Discover curated learning resources using query parameters."""
    try:
        request = LearningResourceRequest(query=query, count=count)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=[
                {"type": e["type"], "loc": e["loc"], "msg": e["msg"]}
                for e in exc.errors()
            ],
        )
    return await _run_discovery(request, service)


@router.post(
    "/select",
    response_model=LearningResourceSelectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a learning resource for later use",
    description="Persist a discovered web resource as a user selection.",
)
def select_learning_resource(
    payload: SelectLearningResourceRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LearningResourceSelectionResponse:
    try:
        selection = resource_selection_service.create_selection(db, user.id, payload)
    except resource_selection_service.InvalidResourceUrlError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except resource_selection_service.DuplicateSelectionError:
        raise HTTPException(
            status_code=409,
            detail="This resource is already in your selected resources.",
        )
    except resource_selection_service.SubjectNotFoundError:
        raise HTTPException(status_code=404, detail="Subject not found")
    return resource_selection_service.to_response(selection)


@router.get(
    "/selected",
    response_model=SelectedResourcesResponse,
    summary="List the user's selected learning resources",
    description="Return the current user's saved web resources, newest first.",
)
def list_selected_resources(
    subject_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SelectedResourcesResponse:
    selections = resource_selection_service.list_selections(
        db, user.id, subject_id=subject_id, limit=limit
    )
    return SelectedResourcesResponse(
        resources=[
            resource_selection_service.to_response(selection)
            for selection in selections
        ],
        count=len(selections),
    )


@router.delete(
    "/selected/{selection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a selected learning resource",
    description="Delete one of the current user's saved web resources.",
)
def delete_selected_resource(
    selection_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    try:
        resource_selection_service.delete_selection(db, selection_id, user.id)
    except resource_selection_service.SelectionNotFoundError:
        raise HTTPException(status_code=404, detail="Selected resource not found")