"""Health check routes."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import engine
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return the service status."""
    return HealthResponse(status="ok", service="ByteBrains API")


@router.get("/health/db")
def health_db() -> JSONResponse:
    """Report whether the database is reachable.

    Kept separate from /health so the basic health check never depends on
    PostgreSQL being available.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )

    return JSONResponse(
        content={"status": "ok", "database": "connected"},
    )