"""Response models for the health check endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Shape of the response returned by GET /health."""

    status: str
    service: str