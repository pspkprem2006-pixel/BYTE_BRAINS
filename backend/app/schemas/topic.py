"""Pydantic schemas for the Topic API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TopicCreate(BaseModel):
    """Payload for creating a topic inside a subject."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    # 0-based display order. Omitted -> appended after the last topic.
    order_index: int | None = Field(default=None, ge=0)


class TopicUpdate(BaseModel):
    """Payload for updating a topic. Every field is optional."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=0)


class TopicResponse(BaseModel):
    """Shape of a topic returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    # The subject a topic belongs to is fixed by the URL during creation.
    subject_id: uuid.UUID
    name: str
    description: str | None
    order_index: int
    created_at: datetime
    updated_at: datetime