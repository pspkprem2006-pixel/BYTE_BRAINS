"""Brave Search provider (server-side only).

The API key travels in the ``X-Subscription-Token`` header and never
appears in URLs, logs, or responses. The raw provider payload is converted
into the normalized ``SearchResult`` model before anything else sees it.
"""

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.search.base import SearchProvider
from app.services.search.errors import (
    WebSearchProviderError,
    WebSearchTimeoutError,
)
from app.services.search.models import MAX_SNIPPET_CHARS, MAX_TITLE_CHARS, SearchResult

logger = logging.getLogger(__name__)

BRAVE_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_HARD_RESULT_LIMIT = 20  # Brave's own maximum for the count parameter.


class BraveSearchProvider(SearchProvider):
    """Search provider backed by the Brave Search API."""

    name = "brave"

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._api_key = (
            api_key if api_key is not None else settings.brave_search_api_key
        )
        self._timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.web_search_timeout_seconds
        )

    async def search(
        self,
        query: str,
        *,
        count: int,
        language: str | None = None,
        country: str | None = None,
        freshness: str | None = None,
    ) -> list[SearchResult]:
        headers = {
            "X-Subscription-Token": self._api_key,
            "Accept": "application/json",
        }
        params = {"q": query, "count": min(count, BRAVE_HARD_RESULT_LIMIT)}
        if language:
            params["lang"] = language
        if country:
            params["country"] = country
        if freshness:
            params["freshness"] = freshness

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(
                    BRAVE_BASE_URL, headers=headers, params=params
                )
        except httpx.TimeoutException:
            raise WebSearchTimeoutError("Web search request timed out.")
        except httpx.RequestError:
            logger.warning("Brave search request failed at the network level")
            raise WebSearchProviderError("Web search provider request failed.")

        # No raw response body is ever logged: content is untrusted and may
        # echo parts of the query or upstream details.
        if response.status_code in (401, 403):
            logger.warning("Brave search rejected the request (status=%s)", response.status_code)
            raise WebSearchProviderError("Web search provider rejected the request.")
        if response.status_code != 200:
            logger.warning("Brave search returned an error (status=%s)", response.status_code)
            raise WebSearchProviderError("Web search provider returned an error.")

        try:
            data = response.json()
        except ValueError:
            raise WebSearchProviderError("Web search provider returned an invalid response.")

        raw_results = None
        if isinstance(data, dict):
            web = data.get("web")
            if isinstance(web, dict):
                raw_results = web.get("results")

        # Brave returns {"web": null} when there are no matches.
        if raw_results is None:
            return []
        if not isinstance(raw_results, list):
            raise WebSearchProviderError(
                "Web search provider returned an unexpected response structure."
            )

        return self._normalize(raw_results)

    def _normalize(self, raw_results: list[object]) -> list[SearchResult]:
        """Convert Brave's results into the normalized internal model."""
        results: list[SearchResult] = []
        for raw in raw_results:
            if not isinstance(raw, dict):
                continue
            try:
                title = str(raw["title"]).strip()
                url = str(raw["url"]).strip()
            except KeyError:
                continue
            if not title or not url:
                continue

            snippet = str(raw.get("description", "") or "").strip()
            domain = urlparse(url).netloc.lower()

            results.append(
                SearchResult(
                    title=title[:MAX_TITLE_CHARS],
                    url=url,
                    domain=domain,
                    snippet=snippet[:MAX_SNIPPET_CHARS],
                    source=self.name,
                    retrieved_at=datetime.now(timezone.utc),
                )
            )
        return results