"""Pydantic schemas for the Tutor API."""

import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TutorAskRequest(BaseModel):
    """Request to ask the AI Tutor a question.

    Either ``material_id`` (uploaded material) or ``subject_id`` (selected
    web resources for a subject) — or both — must be provided.
    """

    material_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    question: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def _at_least_one_source(self) -> "TutorAskRequest":
        if self.material_id is None and self.subject_id is None:
            raise ValueError("material_id or subject_id is required")
        return self


class TutorAskResponse(BaseModel):
    """Response from the AI Tutor."""

    model_config = ConfigDict(from_attributes=True)

    material_id: uuid.UUID | None = None
    question: str
    answer: str


class TutorMessage(BaseModel):
    """A single message in the tutor conversation."""

    role: str  # "user" or "assistant"
    content: str