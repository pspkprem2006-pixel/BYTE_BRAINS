"""Pydantic schemas for the Tutor API."""

import uuid
from pydantic import BaseModel, ConfigDict, Field


class TutorAskRequest(BaseModel):
    """Request to ask the AI Tutor a question."""

    material_id: uuid.UUID
    question: str = Field(min_length=1, max_length=2000)


class TutorAskResponse(BaseModel):
    """Response from the AI Tutor."""

    model_config = ConfigDict(from_attributes=True)

    material_id: uuid.UUID
    question: str
    answer: str


class TutorMessage(BaseModel):
    """A single message in the tutor conversation."""

    role: str  # "user" or "assistant"
    content: str