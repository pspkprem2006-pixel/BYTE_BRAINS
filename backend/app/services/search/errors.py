"""Controlled error types for web search.

Only these types cross the search boundary. Upstream provider errors are
never exposed verbatim to users; the route layer translates these into
safe HTTP responses.
"""


class WebSearchError(Exception):
    """Base class for web search errors."""


class WebSearchNotConfiguredError(WebSearchError):
    """Raised when web search is disabled or no provider API key is set."""


class WebSearchProviderError(WebSearchError):
    """Raised when the search provider fails (network, HTTP, malformed)."""


class WebSearchProviderBoundaryError(WebSearchProviderError):
    """Raised when a provider raises something outside its contract."""


class WebSearchTimeoutError(WebSearchError):
    """Raised when the search provider does not answer in time."""


class InvalidSearchQueryError(WebSearchError):
    """Raised when a query fails service-level validation."""