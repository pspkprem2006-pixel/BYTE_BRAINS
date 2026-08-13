"""Internal normalized representation of a web search result.

Every provider (Brave today, others later) must return these models. The
rest of ByteBrains works only with this representation — provider-specific
response shapes never leak past the provider boundary.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field

MAX_TITLE_CHARS = 300
MAX_SNIPPET_CHARS = 500


class SearchResult(BaseModel):
    """One normalized web search result."""

    title: str = Field(max_length=MAX_TITLE_CHARS)
    url: str
    domain: str = ""
    snippet: str = Field(default="", max_length=MAX_SNIPPET_CHARS)
    source: str
    relevance_score: float | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))