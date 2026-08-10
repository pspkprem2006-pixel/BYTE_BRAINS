"""Health check route."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return the service status."""
    return HealthResponse(status="ok", service="ByteBrains API")