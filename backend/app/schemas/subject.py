"""Pydantic schemas for the Subject API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    """Payload for creating a subject."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class SubjectUpdate(BaseModel):
    """Payload for updating a subject. Every field is optional."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class SubjectResponse(BaseModel):
    """Shape of a subject returned by the API.

    user_id reflects ownership set by the server — the client can never
    choose it (authentication will replace the development user later).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # The ORM column is called "owner_id"; the API exposes it as "user_id".
    user_id: uuid.UUID = Field(validation_alias="owner_id")
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime