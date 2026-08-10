"""ByteBrains API entry point.

Run locally with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, subjects, topics, materials
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Backend API for ByteBrains, an AI-powered adaptive study companion.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(subjects.router)
app.include_router(topics.router)
app.include_router(materials.router)


@app.get("/")
def root() -> dict[str, str]:
    """Simple pointer so a browser visit shows the service name."""
    return {"service": settings.app_name}