"""Web Search REST API routes.

Minimal, extensible endpoint for testing the web search foundation.
Supports both POST (JSON body) and GET (query parameters); both go through
the same validation and the same service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from app.schemas.search import (
    QUERY_MAX_LENGTH,
    RESULT_COUNT_MAX,
    SearchRequest,
    WebSearchResponse,
)
from app.services.search.errors import (
    InvalidSearchQueryError,
    WebSearchError,
    WebSearchNotConfiguredError,
    WebSearchTimeoutError,
)
from app.services.search.service import WebSearchService

router = APIRouter(prefix="/api/search", tags=["search"])


def get_web_search_service() -> WebSearchService:
    """FastAPI dependency: a fresh search service per request."""
    return WebSearchService()


async def _run_search(
    request: SearchRequest,
    service: WebSearchService,
) -> WebSearchResponse:
    try:
        results = await service.search(
            request.query,
            count=request.count,
            language=request.language,
            country=request.country,
            freshness=request.freshness,
        )
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
            detail="Web search is temporarily unavailable. Please try again.",
        )
    return WebSearchResponse(results=results)


@router.post("", response_model=WebSearchResponse)
async def search_web(
    request: SearchRequest,
    service: WebSearchService = Depends(get_web_search_service),
) -> WebSearchResponse:
    """Search the web through the configured provider."""
    return await _run_search(request, service)


@router.get("", response_model=WebSearchResponse)
async def search_web_get(
    q: str = Query(default="", max_length=QUERY_MAX_LENGTH),
    count: int | None = Query(default=None, ge=1, le=RESULT_COUNT_MAX),
    language: str | None = Query(default=None, pattern=r"^[a-z]{2}$"),
    country: str | None = Query(default=None, pattern=r"^[a-z]{2}$"),
    freshness: str | None = Query(default=None),
    service: WebSearchService = Depends(get_web_search_service),
) -> WebSearchResponse:
    """Search the web using query parameters."""
    # Reusing SearchRequest gives GET the exact same validation as POST
    # (blank queries, freshness values, ...).
    try:
        request = SearchRequest(
            query=q,
            count=count,
            language=language,
            country=country,
            freshness=freshness,
        )
    except ValidationError as exc:
        # FastAPI's own 422 format, minus the non-serializable ctx entries.
        raise HTTPException(
            status_code=422,
            detail=[
                {"type": e["type"], "loc": e["loc"], "msg": e["msg"]}
                for e in exc.errors()
            ],
        )
    return await _run_search(request, service)