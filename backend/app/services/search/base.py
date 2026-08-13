"""Provider-independent search abstraction.

Application code (and ``WebSearchService``) depends on ``SearchProvider``,
never on a concrete provider. Adding a second provider later means
implementing this interface and swapping the instance — no other layer
changes.
"""

from abc import ABC, abstractmethod

from app.services.search.models import SearchResult


class SearchProvider(ABC):
    """Interface every search provider must implement."""

    name: str

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        count: int,
        language: str | None = None,
        country: str | None = None,
        freshness: str | None = None,
    ) -> list[SearchResult]:
        """Run a search and return normalized results.

        Raises ``WebSearchError`` subclasses on failure; upstream details
        are never exposed through this method.
        """