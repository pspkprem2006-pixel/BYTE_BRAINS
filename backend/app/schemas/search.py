"""Pydantic schemas for the Web Search API.

Limits are conservative: short queries, few results, capped snippet size.
Request validation happens here, so the route layer stays thin.

The response reuses the normalized internal result model, so the API
contract is provider-independent by construction.
"""

from typing import List

from pydantic import BaseModel, Field, field_validator

from app.services.search.models import SearchResult

QUERY_MAX_LENGTH = 300
RESULT_COUNT_MIN = 1
RESULT_COUNT_MAX = 10
FRESHNESS_VALUES = frozenset({"pd", "pw", "pm", "py"})


class SearchRequest(BaseModel):
    """Request to search the web through the configured provider."""

    query: str = Field(min_length=1, max_length=QUERY_MAX_LENGTH)
    count: int | None = Field(
        default=None, ge=RESULT_COUNT_MIN, le=RESULT_COUNT_MAX
    )
    language: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    country: str | None = Field(default=None, pattern=r"^[a-z]{2}$")
    freshness: str | None = Field(default=None)

    @field_validator("query")
    @classmethod
    def _query_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be blank")
        return stripped

    @field_validator("freshness")
    @classmethod
    def _freshness_must_be_supported(cls, value: str | None) -> str | None:
        if value is not None and value not in FRESHNESS_VALUES:
            raise ValueError("freshness must be one of: pd, pw, pm, py")
        return value


class WebSearchResponse(BaseModel):
    """Normalized web search response (never the raw provider payload)."""

    results: List[SearchResult]