"""Pydantic schemas for the Material API."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MaterialCreate(BaseModel):
    """Payload for creating a material (used internally by service)."""

    subject_id: uuid.UUID


class MaterialResponse(BaseModel):
    """Shape of a material returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject_id: uuid.UUID | None
    filename: str
    original_filename: str
    file_type: str
    file_size: int | None
    processing_status: str
    created_at: datetime
    updated_at: datetime