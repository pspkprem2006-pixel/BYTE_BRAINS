"""Pydantic schemas for the Learning Resources API.

The response is a clean, provider-independent description of useful learning
material found on the web. It is derived from normalized search results and
never leaks provider-specific payloads or API keys.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator

QUERY_MAX_LENGTH = 300
RESOURCE_COUNT_MIN = 1
RESOURCE_COUNT_MAX = 10

ResourceType = Enum(
    "ResourceType",
    {
        "official_docs": "official_docs",
        "tutorial": "tutorial",
        "article": "article",
        "video": "video",
        "practice": "practice",
        "reference": "reference",
        "course": "course",
        "other": "other",
    },
)


class LearningResourceRequest(BaseModel):
    """Request to discover learning resources for a topic."""

    query: str = Field(min_length=1, max_length=QUERY_MAX_LENGTH)
    count: int | None = Field(
        default=None, ge=RESOURCE_COUNT_MIN, le=RESOURCE_COUNT_MAX
    )

    @field_validator("query")
    @classmethod
    def _query_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped


class LearningResource(BaseModel):
    """One curated learning resource, ready to be presented to the user."""

    title: str = Field(max_length=300)
    url: str
    domain: str = ""
    description: str = Field(default="", max_length=500)
    resource_type: ResourceType = ResourceType.other
    is_official: bool = False
    difficulty: str | None = Field(
        default=None, pattern=r"^(beginner|intermediate|advanced)$"
    )
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str
    retrieved_at: datetime
    topic: str


class LearningResourcesResponse(BaseModel):
    """Curated learning resources for one topic."""

    query: str
    resources: List[LearningResource]


SELECTION_TITLE_MAX = 300
SELECTION_URL_MAX = 500
SELECTION_DESCRIPTION_MAX = 1000
SELECTIONS_LIST_LIMIT = 100


class SelectLearningResourceRequest(BaseModel):
    """Request to save a discovered web resource for later use."""

    subject_id: uuid.UUID | None = None
    title: str = Field(min_length=1, max_length=SELECTION_TITLE_MAX)
    url: str = Field(min_length=1, max_length=SELECTION_URL_MAX)
    domain: str = Field(default="", max_length=255)
    resource_type: ResourceType = ResourceType.other
    is_official: bool = False
    difficulty: str | None = Field(
        default=None, pattern=r"^(beginner|intermediate|advanced)$"
    )
    description: str = Field(default="", max_length=SELECTION_DESCRIPTION_MAX)
    source: str = Field(default="web_search", max_length=50)

    @field_validator("title")
    @classmethod
    def _title_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        return stripped


class LearningResourceSelectionResponse(BaseModel):
    """One persisted learning-resource selection."""

    id: uuid.UUID
    subject_id: uuid.UUID | None
    title: str
    url: str
    domain: str
    resource_type: ResourceType
    is_official: bool
    difficulty: str | None
    description: str
    source: str
    created_at: datetime
    last_used_at: datetime | None


class SelectedResourcesResponse(BaseModel):
    """The user's persisted learning-resource selections."""

    resources: List[LearningResourceSelectionResponse]
    count: int