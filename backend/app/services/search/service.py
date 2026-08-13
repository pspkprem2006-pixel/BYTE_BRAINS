"""Web search service: query validation, limits, provider invocation.

The service is the only entry point application code uses. It owns:
- query validation (length, blank checks)
- result caps
- retry policy for transient provider failures
- mapped, controlled errors (upstream details never escape)
- a graceful "not configured" behavior when the API key is missing
"""

import logging

from app.core.config import settings
from app.schemas.search import QUERY_MAX_LENGTH, RESULT_COUNT_MAX
from app.services.search.base import SearchProvider
from app.services.search.brave import BraveSearchProvider
from app.services.search.errors import (
    InvalidSearchQueryError,
    WebSearchError,
    WebSearchNotConfiguredError,
    WebSearchProviderBoundaryError,
    WebSearchTimeoutError,
)
from app.services.search.models import SearchResult

logger = logging.getLogger(__name__)

SEARCH_RETRY_ATTEMPTS = 2


class WebSearchService:
    """Provider-independent facade for web search."""

    def __init__(
        self,
        provider: SearchProvider | None = None,
        *,
        max_results: int | None = None,
    ) -> None:
        self._provider: SearchProvider = (
            provider if provider is not None else BraveSearchProvider()
        )
        self._max_results = (
            max_results
            if max_results is not None
            else settings.web_search_max_results
        )

    @property
    def is_configured(self) -> bool:
        """Web search is usable only when enabled AND a key is set."""
        return settings.web_search_enabled and bool(settings.brave_search_api_key)

    def _validate_query(self, query: str) -> str:
        if not isinstance(query, str) or not query.strip():
            raise InvalidSearchQueryError("Query must not be empty.")
        if len(query) > QUERY_MAX_LENGTH:
            raise InvalidSearchQueryError(
                f"Query must be at most {QUERY_MAX_LENGTH} characters."
            )
        return query.strip()

    async def search(
        self,
        query: str,
        *,
        count: int | None = None,
        language: str | None = None,
        country: str | None = None,
        freshness: str | None = None,
    ) -> list[SearchResult]:
        """Run a web search and return normalized results."""
        validated_query = self._validate_query(query)

        if not self.is_configured:
            raise WebSearchNotConfiguredError("Web search is not configured.")

        result_count = (
            min(count, self._max_results)
            if count is not None
            else self._max_results
        )
        result_count = max(1, min(result_count, RESULT_COUNT_MAX))

        attempts = 0
        last_error: WebSearchError | None = None
        while attempts < SEARCH_RETRY_ATTEMPTS:
            attempts += 1
            try:
                return await self._provider.search(
                    validated_query,
                    count=result_count,
                    language=language,
                    country=country,
                    freshness=freshness,
                )
            except WebSearchTimeoutError:
                # Delaying then retrying a timed-out upstream call usually
                # makes the timeout worse; surface it immediately.
                raise
            except WebSearchError as exc:
                last_error = exc
                logger.warning(
                    "Web search attempt %s/%s failed (%s)",
                    attempts,
                    SEARCH_RETRY_ATTEMPTS,
                    type(exc).__name__,
                )
            except Exception:  # pragma: no cover - defensive boundary
                # Never let an unexpected provider bug escape as a raw error.
                logger.exception("Web search provider raised an unexpected error")
                raise WebSearchProviderBoundaryError() from None

        # Only the generic, controlled error is re-raised.
        assert last_error is not None
        raise last_error