"""Quality control for discovered learning resources.

Steps applied to the merged set of search results before ranking:
- normalize domains and URLs
- drop clearly irrelevant or broken results
- remove duplicates (same URL, or same title + domain)

This module works on the normalized ``SearchResult`` models produced by the
search layer; it never touches raw provider payloads.
"""

import ipaddress
import re
from urllib.parse import parse_qsl, urlparse, urlunparse

from app.services.learning_resources.classifier import normalize_domain
from app.services.search.models import SearchResult

_JUNK_TITLE_PATTERNS = (
    re.compile(r"\b(404|not found|page not found|error 404)\b", re.IGNORECASE),
    re.compile(r"\b(domain|this domain).{0,30}(for sale)\b", re.IGNORECASE),
    re.compile(r"\b(buy this domain|domain auction)\b", re.IGNORECASE),
)
_JUNK_URL_PATTERNS = (
    re.compile(r"\b(error\s*404|not-found)\b", re.IGNORECASE),
)
# Pages that are not learning content: matched only against the last path
# segment, so a tutorial like ".../build-a-login-form" is NOT filtered.
_JUNK_LAST_PATH_SEGMENT = re.compile(
    r"^(login|signin|sign-in|signup|sign-up|register|checkout|cart|account)$",
    re.IGNORECASE,
)

TRACKING_QUERY_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "mc_cid",
        "mc_eid",
    }
)

MAX_CANONICAL_URL_LENGTH = 500


def _is_private_network_host(host: str) -> bool:
    """True for localhost and private/reserved network addresses.

    The backend never fetches user URLs, but a "learning resource" pointing
    at localhost or a private network is never legitimate and must not be
    persisted or fed to the AI as reference material.
    """
    host = host.lower()
    if host == "localhost" or host.endswith(".localhost"):
        return True
    if host.endswith((".local", ".internal")):
        return True
    if not host or not (host[0].isdigit() or host[0] in ("[", ":")):
        return False
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    return not ip.is_global or ip.is_loopback or ip.is_link_local or ip.is_reserved


def canonical_resource_url(url: str) -> str:
    """Normalize a URL for persistence.

    Rules:
    - only http/https schemes are accepted (others return "")
    - host is lowercased (www prefix kept as given)
    - localhost and private/reserved network hosts are rejected ("")
    - the fragment is dropped
    - common tracking parameters are removed
    - the result is capped at MAX_CANONICAL_URL_LENGTH
    """
    try:
        parts = urlparse(url.strip())
    except ValueError:
        return ""
    if parts.scheme.lower() not in ("http", "https"):
        return ""
    if not parts.netloc:
        return ""
    if "@" in parts.netloc:
        return ""  # credentials in URLs are never persisted
    host = parts.netloc.lower()
    if ":" in host and not host.startswith("["):
        check_host = host.split(":", 1)[0]
    elif host.startswith("[") and "]" in host:
        check_host = host[1:].split("]", 1)[0]
    else:
        check_host = host
    if _is_private_network_host(check_host):
        return ""
    query = "&".join(
        f"{key}={value}"
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_PARAMS
    )
    canonical = urlunparse(
        (parts.scheme.lower(), host, parts.path or "/", parts.params, query, "")
    )
    return canonical[:MAX_CANONICAL_URL_LENGTH]


def normalized_url(url: str) -> str:
    """Canonical form of a URL used for deduplication.

    Scheme and ``www.`` prefix are dropped, the host is lowercased, the
    fragment is removed, and common tracking parameters are stripped. The
    original URL is always kept for display.
    """
    try:
        parts = urlparse(url)
    except ValueError:
        return url.strip().rstrip("/").lower()
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    query = "&".join(
        f"{key}={value}"
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_QUERY_PARAMS
    )
    canonical = urlunparse(
        ("", host, parts.path.rstrip("/") or "/", parts.params, query, "")
    )
    return canonical.lower()


def normalized_title(title: str) -> str:
    """Whitespace-normalized, lowercased title used for near-duplicate checks."""
    return " ".join(title.lower().split())


def is_irrelevant(result: SearchResult) -> bool:
    """True when a result should not be presented as a learning resource."""
    url = result.url.strip()
    if not url.lower().startswith(("http://", "https://")):
        return True
    if not result.domain:
        return True
    if not result.title:
        return True
    if any(pattern.search(result.title) for pattern in _JUNK_TITLE_PATTERNS):
        return True
    if any(pattern.search(url) for pattern in _JUNK_URL_PATTERNS):
        return True
    try:
        path = urlparse(url).path.rstrip("/")
    except ValueError:
        path = ""
    if path and _JUNK_LAST_PATH_SEGMENT.search(path.rsplit("/", 1)[-1]):
        return True
    return False


def deduplicate(results: list[SearchResult]) -> list[SearchResult]:
    """Remove duplicates, keeping the first occurrence (best ranked query).

    A result is a duplicate when its normalized URL matches, or when both
    its normalized title and its normalized domain match (the same resource
    surfaced through different queries/URLs).
    """
    seen_urls: set[str] = set()
    seen_title_domains: set[tuple[str, str]] = set()
    deduped: list[SearchResult] = []
    for result in results:
        url_key = normalized_url(result.url)
        title_key = normalized_title(result.title)
        title_domain_key = (title_key, normalize_domain(result.domain))
        if not url_key:
            continue
        if url_key in seen_urls:
            continue
        if title_domain_key in seen_title_domains:
            continue
        seen_urls.add(url_key)
        seen_title_domains.add(title_domain_key)
        deduped.append(result)
    return deduped