"""Tests for the Web Search foundation.

Coverage:
- valid search, empty/blank/oversized queries
- result normalization (provider-level)
- provider failure, timeout, malformed upstream response
- result limits and no-results handling
- missing API key / disabled web search (graceful "not configured")
- API response schema and GET/POST parity
- the API key never appears in any response

The Brave provider is always mocked: no real network calls happen here.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.routes.search import get_web_search_service
from app.core.config import settings
from app.main import app
from app.services.search.service import WebSearchService
from app.services.search.brave import BRAVE_BASE_URL, BraveSearchProvider
from app.services.search.errors import (
    WebSearchNotConfiguredError,
    WebSearchProviderError,
    WebSearchTimeoutError,
)
from app.services.search.models import MAX_SNIPPET_CHARS, MAX_TITLE_CHARS, SearchResult

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeResponse:
    """Minimal stand-in for an httpx.Response."""

    def __init__(self, status_code: int, payload: object):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeProvider:
    """In-memory SearchProvider used to exercise the service boundary."""

    name = "brave"

    def __init__(self, results=None, error=None):
        self.results = results or []
        self.error = error
        self.calls = []

    async def search(self, query, *, count, language=None, country=None, freshness=None):
        self.calls.append(
            {
                "query": query,
                "count": count,
                "language": language,
                "country": country,
                "freshness": freshness,
            }
        )
        if self.error:
            raise self.error
        return self.results


class ErrorStubService:
    """Route-level stand-in that raises a specific WebSearchError."""

    def __init__(self, error):
        self._error = error

    async def search(self, query, **kwargs):
        raise self._error


@pytest.fixture
def enable_search(monkeypatch):
    """Give settings a fake key so is_configured is True."""
    monkeypatch.setattr(settings, "brave_search_api_key", "test-brave-key")
    monkeypatch.setattr(settings, "web_search_enabled", True)
    monkeypatch.setattr(settings, "web_search_max_results", 5)
    yield


@pytest.fixture
def override_service():
    """Override the /api/search dependency with a controllable service."""

    def _override(service):
        app.dependency_overrides[get_web_search_service] = lambda: service

    yield _override
    app.dependency_overrides.clear()


def _sample_payload(results=None):
    if results is None:
        results = [
            {
                "title": "PostgreSQL Joins Explained",
                "url": "https://www.example.com/postgresql-joins",
                "description": "A clear guide to JOIN types in PostgreSQL.",
                "age": "12 days",
            }
        ]
    return {"web": {"results": results}}


def _patched_client(mock_async_client, response):
    """Wire the patched httpx.AsyncClient so .get returns `response`."""
    instance = mock_async_client.return_value.__aenter__.return_value
    instance.get = AsyncMock(return_value=response)
    return instance


def _valid_result() -> SearchResult:
    return SearchResult(
        title="PostgreSQL Joins",
        url="https://www.postgresql.org/docs/current/queries-table-expressions.html",
        domain="www.postgresql.org",
        snippet="JOIN types for combining tables.",
        source="brave",
    )


# ---------------------------------------------------------------------------
# Provider-level: normalization and upstream failures (httpx mocked)
# ---------------------------------------------------------------------------


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_normalizes_results(mock_async_client):
    instance = _patched_client(mock_async_client, FakeResponse(200, _sample_payload()))
    provider = BraveSearchProvider(api_key="test-key")

    results = asyncio.run(provider.search("postgresql joins", count=3))

    assert len(results) == 1
    result = results[0]
    assert result.title == "PostgreSQL Joins Explained"
    assert result.url == "https://www.example.com/postgresql-joins"
    assert result.domain == "www.example.com"
    assert result.snippet == "A clear guide to JOIN types in PostgreSQL."
    assert result.source == "brave"
    assert result.retrieved_at is not None

    # The key travels as a header, never in the URL/params.
    instance.get.assert_awaited_once()
    call = instance.get.await_args
    assert call.kwargs["headers"]["X-Subscription-Token"] == "test-key"
    assert call.args[0] == BRAVE_BASE_URL
    assert "X-Subscription-Token" not in str(call.kwargs["params"])


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_supports_count_language_country_freshness(mock_async_client):
    instance = _patched_client(mock_async_client, FakeResponse(200, _sample_payload()))
    provider = BraveSearchProvider(api_key="test-key")

    asyncio.run(
        provider.search("sql", count=7, language="en", country="us", freshness="pw")
    )

    call = instance.get.await_args
    params = dict(call.kwargs["params"])
    assert params["count"] == 7
    assert params["lang"] == "en"
    assert params["country"] == "us"
    assert params["freshness"] == "pw"


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_caps_count_at_brave_limit(mock_async_client):
    instance = _patched_client(mock_async_client, FakeResponse(200, _sample_payload()))
    provider = BraveSearchProvider(api_key="test-key")

    asyncio.run(provider.search("sql", count=999))

    assert dict(instance.get.await_args.kwargs["params"])["count"] == 20


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_truncates_title_and_snippet(mock_async_client):
    payload = _sample_payload(
        [
            {
                "title": "T" * 500,
                "url": "https://www.example.com/x",
                "description": "S" * 2000,
            }
        ]
    )
    _patched_client(mock_async_client, FakeResponse(200, payload))
    provider = BraveSearchProvider(api_key="test-key")

    results = asyncio.run(provider.search("sql", count=1))

    assert len(results[0].title) <= MAX_TITLE_CHARS
    assert len(results[0].snippet) <= MAX_SNIPPET_CHARS


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_no_results_returns_empty_list(mock_async_client):
    _patched_client(mock_async_client, FakeResponse(200, {"web": None}))
    provider = BraveSearchProvider(api_key="test-key")

    results = asyncio.run(provider.search("nothing found", count=5))

    assert results == []


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_skips_malformed_rows(mock_async_client):
    payload = _sample_payload(
        [
            {"url": "https://missing-title.com"},  # no title -> skipped
            "not-a-dict",  # -> skipped
            {"title": "", "url": "https://blank-title.com"},  # blank -> skipped
            {"title": "Good", "url": "https://good.example.com", "description": "ok"},
        ]
    )
    _patched_client(mock_async_client, FakeResponse(200, payload))
    provider = BraveSearchProvider(api_key="test-key")

    results = asyncio.run(provider.search("sql", count=5))

    assert len(results) == 1
    assert results[0].title == "Good"


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_malformed_json_raises_controlled_error(mock_async_client):
    _patched_client(mock_async_client, FakeResponse(200, ValueError("bad json")))
    provider = BraveSearchProvider(api_key="test-key")

    with pytest.raises(WebSearchProviderError):
        asyncio.run(provider.search("sql", count=1))


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_unexpected_structure_raises_controlled_error(mock_async_client):
    _patched_client(mock_async_client, FakeResponse(200, {"web": {"results": "nope"}}))
    provider = BraveSearchProvider(api_key="test-key")

    with pytest.raises(WebSearchProviderError):
        asyncio.run(provider.search("sql", count=1))


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_http_error_raises_controlled_error(mock_async_client):
    _patched_client(mock_async_client, FakeResponse(500, {"error": "upstream detail"}))
    provider = BraveSearchProvider(api_key="test-key")

    with pytest.raises(WebSearchProviderError):
        asyncio.run(provider.search("sql", count=1))


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_401_raises_controlled_error(mock_async_client):
    _patched_client(mock_async_client, FakeResponse(401, {"message": "unauthorized"}))
    provider = BraveSearchProvider(api_key="test-key")

    with pytest.raises(WebSearchProviderError):
        asyncio.run(provider.search("sql", count=1))


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_network_failure_raises_controlled_error(mock_async_client):
    import httpx

    instance = _patched_client(mock_async_client, FakeResponse(200, {}))
    instance.get = AsyncMock(side_effect=httpx.ConnectError("no route to host"))
    provider = BraveSearchProvider(api_key="test-key")

    with pytest.raises(WebSearchProviderError):
        asyncio.run(provider.search("sql", count=1))


@patch("app.services.search.brave.httpx.AsyncClient")
def test_provider_timeout_raises_timeout_error(mock_async_client):
    import httpx

    instance = _patched_client(mock_async_client, FakeResponse(200, {}))
    instance.get = AsyncMock(side_effect=httpx.TimeoutException("read timed out"))
    provider = BraveSearchProvider(api_key="test-key")

    with pytest.raises(WebSearchTimeoutError):
        asyncio.run(provider.search("sql", count=1))


# ---------------------------------------------------------------------------
# Service-level: validation, limits, config, retry
# ---------------------------------------------------------------------------


def test_service_delegates_and_trims_query(enable_search, monkeypatch):
    provider = FakeProvider(results=[_valid_result()])
    service = WebSearchService(provider=provider, max_results=5)

    results = asyncio.run(service.search("  postgresql joins  ", count=5))

    assert len(results) == 1
    assert provider.calls[0]["query"] == "postgresql joins"
    assert provider.calls[0]["count"] == 5


def test_service_clamps_requested_count_to_max_results(enable_search):
    provider = FakeProvider(results=[_valid_result()])
    service = WebSearchService(provider=provider, max_results=3)

    asyncio.run(service.search("sql", count=10))

    assert provider.calls[0]["count"] == 3


def test_service_clamps_max_results_to_hard_limit(enable_search, monkeypatch):
    monkeypatch.setattr(settings, "web_search_max_results", 100)
    provider = FakeProvider(results=[_valid_result()])
    service = WebSearchService(provider=provider)

    asyncio.run(service.search("sql"))

    assert provider.calls[0]["count"] == 10


def test_service_rejects_blank_query(enable_search):
    service = WebSearchService(provider=FakeProvider())
    with pytest.raises(Exception) as exc_info:
        asyncio.run(service.search("   "))
    from app.services.search.errors import InvalidSearchQueryError

    assert isinstance(exc_info.value, InvalidSearchQueryError)


def test_service_rejects_oversized_query(enable_search):
    service = WebSearchService(provider=FakeProvider())
    from app.services.search.errors import InvalidSearchQueryError

    with pytest.raises(InvalidSearchQueryError):
        asyncio.run(service.search("x" * 301))


def test_service_not_configured_without_key(monkeypatch):
    monkeypatch.setattr(settings, "brave_search_api_key", "")
    monkeypatch.setattr(settings, "web_search_enabled", True)
    service = WebSearchService(provider=FakeProvider())

    with pytest.raises(WebSearchNotConfiguredError):
        asyncio.run(service.search("sql"))


def test_service_not_configured_when_disabled(enable_search, monkeypatch):
    monkeypatch.setattr(settings, "web_search_enabled", False)
    service = WebSearchService(provider=FakeProvider())

    with pytest.raises(WebSearchNotConfiguredError):
        asyncio.run(service.search("sql"))


def test_service_retries_once_and_succeeds(enable_search):
    provider = FakeProvider(results=[_valid_result()])

    async def flaky_search(query, *, count, language=None, country=None, freshness=None):
        provider.calls.append(
            {
                "query": query,
                "count": count,
                "language": language,
                "country": country,
                "freshness": freshness,
            }
        )
        if len(provider.calls) == 1:
            raise WebSearchProviderError("transient")
        return [_valid_result()]

    provider.search = flaky_search
    service = WebSearchService(provider=provider)

    results = asyncio.run(service.search("sql", count=5))

    assert len(results) == 1
    assert len(provider.calls) == 2


def test_service_gives_up_after_retries(enable_search):
    provider = FakeProvider(error=WebSearchProviderError("always down"))
    service = WebSearchService(provider=provider)

    with pytest.raises(WebSearchProviderError):
        asyncio.run(service.search("sql", count=5))
    assert len(provider.calls) == 2  # initial attempt + 1 retry


def test_service_does_not_retry_timeouts(enable_search):
    provider = FakeProvider(error=WebSearchTimeoutError("slow"))
    service = WebSearchService(provider=provider)

    with pytest.raises(WebSearchTimeoutError):
        asyncio.run(service.search("sql", count=5))
    assert len(provider.calls) == 1


def test_service_maps_unexpected_provider_bugs_to_controlled_error(enable_search):
    provider = FakeProvider()

    async def broken_search(query, **kwargs):
        raise RuntimeError("provider bug")

    provider.search = broken_search
    service = WebSearchService(provider=provider)

    with pytest.raises(WebSearchProviderError):
        asyncio.run(service.search("sql", count=5))


# ---------------------------------------------------------------------------
# Route-level: API contract, validation errors, safe failures
# ---------------------------------------------------------------------------


def test_post_valid_search_returns_normalized_results(enable_search, override_service):
    override_service(WebSearchService(provider=FakeProvider(results=[_valid_result()])))

    response = client.post("/api/search", json={"query": "PostgreSQL joins"})

    assert response.status_code == 200
    body = response.json()
    assert sorted(body.keys()) == ["results"]
    results = body["results"]
    assert len(results) == 1
    result = results[0]
    assert result["title"] == "PostgreSQL Joins"
    assert result["url"].startswith("https://")
    assert result["domain"] == "www.postgresql.org"
    assert result["snippet"]
    assert result["source"] == "brave"
    assert "retrieved_at" in result


def test_post_empty_query_returns_422(override_service):
    override_service(ErrorStubService(WebSearchProviderError("unused")))

    response = client.post("/api/search", json={"query": ""})

    assert response.status_code == 422


def test_post_blank_query_returns_422(override_service):
    override_service(ErrorStubService(WebSearchProviderError("unused")))

    response = client.post("/api/search", json={"query": "   "})

    assert response.status_code == 422


def test_post_oversized_query_returns_422(override_service):
    override_service(ErrorStubService(WebSearchProviderError("unused")))

    response = client.post("/api/search", json={"query": "x" * 301})

    assert response.status_code == 422


def test_post_count_bounds_return_422(override_service):
    override_service(ErrorStubService(WebSearchProviderError("unused")))

    assert client.post("/api/search", json={"query": "sql", "count": 0}).status_code == 422
    assert client.post("/api/search", json={"query": "sql", "count": 11}).status_code == 422


def test_post_invalid_language_and_country_return_422(override_service):
    override_service(ErrorStubService(WebSearchProviderError("unused")))

    assert (
        client.post("/api/search", json={"query": "sql", "language": "EN"}).status_code
        == 422
    )
    assert (
        client.post("/api/search", json={"query": "sql", "country": "USA"}).status_code
        == 422
    )


def test_post_invalid_freshness_returns_422(override_service):
    override_service(ErrorStubService(WebSearchProviderError("unused")))

    response = client.post("/api/search", json={"query": "sql", "freshness": "tomorrow"})

    assert response.status_code == 422
    assert "freshness" in str(response.json()["detail"])


def test_post_no_results_returns_empty_list(enable_search, override_service):
    override_service(WebSearchService(provider=FakeProvider(results=[])))

    response = client.post("/api/search", json={"query": "nothing on the web"})

    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_post_provider_failure_returns_503_generic(enable_search, override_service):
    override_service(WebSearchService(provider=FakeProvider(error=WebSearchProviderError("boom"))))

    response = client.post("/api/search", json={"query": "sql"})

    assert response.status_code == 503
    assert "boom" not in response.json()["detail"].lower()
    assert "temporarily unavailable" in response.json()["detail"].lower()


def test_post_timeout_returns_504(enable_search, override_service):
    override_service(WebSearchService(provider=FakeProvider(error=WebSearchTimeoutError("slow"))))

    response = client.post("/api/search", json={"query": "sql"})

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


def test_missing_api_key_returns_503_not_configured(monkeypatch, override_service):
    monkeypatch.setattr(settings, "brave_search_api_key", "")
    monkeypatch.setattr(settings, "web_search_enabled", True)
    override_service(WebSearchService())

    response = client.post("/api/search", json={"query": "sql"})

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_get_valid_search_returns_normalized_results(enable_search, override_service):
    override_service(WebSearchService(provider=FakeProvider(results=[_valid_result()])))

    response = client.get("/api/search", params={"q": "PostgreSQL joins", "count": 3})

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 1
    assert body["results"][0]["source"] == "brave"


def test_get_blank_query_returns_422(override_service):
    override_service(ErrorStubService(WebSearchProviderError("unused")))

    response = client.get("/api/search", params={"q": "   "})

    assert response.status_code == 422


def test_api_key_never_appears_in_success_response(enable_search, override_service):
    override_service(WebSearchService(provider=FakeProvider(results=[_valid_result()])))

    response = client.post("/api/search", json={"query": "brave key leak check"})

    assert "test-brave-key" not in response.text
    assert "X-Subscription-Token" not in response.text


def test_api_key_never_appears_in_error_response(enable_search, override_service):
    override_service(WebSearchService(provider=FakeProvider(error=WebSearchProviderError("x"))))

    response = client.post("/api/search", json={"query": "sql"})

    assert "test-brave-key" not in response.text


def test_search_has_no_side_effect_on_existing_apis():
    """Sanity: the new router did not disturb existing endpoints."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()