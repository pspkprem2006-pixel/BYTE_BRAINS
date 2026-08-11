"""Pydantic schemas for the Progress API."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ProgressItem(BaseModel):
    """A user's mastery of one topic, as tracked by UserProgress."""

    topic_id: uuid.UUID
    topic_name: str
    subject_id: uuid.UUID
    subject_name: str
    mastery_score: int
    topics_completed: int
    last_studied_at: datetime | None
