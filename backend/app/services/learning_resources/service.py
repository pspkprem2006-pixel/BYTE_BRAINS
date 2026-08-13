"""Learning resource discovery on top of the search abstraction.

``LearningResourceService`` depends only on ``WebSearchService`` (and thus
on the ``SearchProvider`` interface), never on a concrete provider. It:

1. turns a topic into a small, controlled set of query variants
2. runs those searches through the search layer
3. filters out junk, removes duplicates, normalizes domains
4. classifies resource types and official sources
5. ranks and truncates to the requested count

The result is a list of ``LearningResource`` models — the contract future
features (tutor context, quiz generation, study plans) will consume.
"""

import logging
import re

from app.core.config import settings
from app.schemas.learning_resources import (
    RESOURCE_COUNT_MAX,
    LearningResource,
    LearningResourceRequest,
)
from app.services.learning_resources.classifier import (
    classify_resource_type,
    detect_difficulty,
    extract_domain,
    is_official_domain,
    normalize_domain,
)
from app.services.learning_resources.quality import (
    deduplicate,
    is_irrelevant,
    normalized_url,
)
from app.services.learning_resources.ranking import RankedResult, score_result, sort_by_score
from app.services.search.errors import (
    InvalidSearchQueryError,
    WebSearchError,
    WebSearchNotConfiguredError,
    WebSearchTimeoutError,
)
from app.services.search.service import WebSearchService

logger = logging.getLogger(__name__)

QUERY_VARIANT_SUFFIXES = (
    "",
    " tutorial",
    " official documentation",
    " beginner guide",
    " practice exercises",
)

_TOPIC_TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}")


def _topic_words(query: str) -> frozenset[str]:
    """Significant words of the topic, used for title-match ranking."""
    return frozenset(_TOPIC_TOKEN_PATTERN.findall(query.lower()))


class LearningResourceService:
    """Discover, curate, and rank learning resources for a topic."""

    def __init__(
        self,
        search_service: WebSearchService | None = None,
        *,
        trusted_domains: frozenset[str] | None = None,
        max_queries: int | None = None,
    ) -> None:
        self._search = search_service or WebSearchService()
        self._trusted_domains = (
            trusted_domains
            if trusted_domains is not None
            else self._parse_trusted_domains(settings.web_search_trusted_domains)
        )
        self._max_queries = (
            max_queries
            if max_queries is not None
            else settings.web_search_learning_max_queries
        )

    @staticmethod
    def _parse_trusted_domains(raw: str) -> frozenset[str]:
        return frozenset(
            normalize_domain(part)
            for part in (raw or "").split(",")
            if normalize_domain(part)
        )

    def _query_variants(self, topic: str, max_queries: int) -> list[str]:
        """Controlled query variants: plain topic first, then focused ones."""
        variants = [f"{topic}{suffix}".strip() for suffix in QUERY_VARIANT_SUFFIXES]
        return variants[: max(1, min(max_queries, len(variants)))]

    async def discover(
        self, request: LearningResourceRequest
    ) -> list[LearningResource]:
        topic = request.query.strip()
        if not topic:
            raise InvalidSearchQueryError("Query must not be empty.")
        if not self._search.is_configured:
            raise WebSearchNotConfiguredError("Web search is not configured.")

        count = request.count if request.count is not None else RESOURCE_COUNT_MAX
        count = max(1, min(count, RESOURCE_COUNT_MAX))

        queries = self._query_variants(topic, self._max_queries)
        topic_word_set = _topic_words(topic)

        raw_results: list[tuple[str, int, int, object]] = []
        last_error: WebSearchError | None = None
        for query in queries:
            try:
                results = await self._search.search(query, count=count)
            except WebSearchTimeoutError:
                raise
            except WebSearchError as exc:
                # One failed variant must not sink the whole discovery; only
                # when every variant fails is the error surfaced.
                last_error = exc
                logger.warning(
                    "Learning resource query variant failed (%s)",
                    type(exc).__name__,
                )
                continue
            for position, result in enumerate(results):
                raw_results.append((query, position, len(results), result))
        if not raw_results and last_error is not None:
            raise last_error

        return self._curate(
            raw_results,
            topic=topic,
            topic_word_set=topic_word_set,
            count=count,
        )

    def _curate(
        self,
        raw_results: list[tuple[str, int, int, object]],
        *,
        topic: str,
        topic_word_set: frozenset[str],
        count: int,
    ) -> list[LearningResource]:
        """Filter, deduplicate, classify, rank, and truncate results."""
        candidates = [
            (query, position, total, result)
            for query, position, total, result in raw_results
            if not is_irrelevant(result)
        ]

        occurrences: dict[str, int] = {}
        for _query, _position, _total, result in candidates:
            key = f"{normalized_url(result.url)}|{normalize_domain(result.domain)}"
            occurrences[key] = occurrences.get(key, 0) + 1

        deduped_results = deduplicate(
            [result for _q, _p, _t, result in candidates]
        )
        kept_keys = {
            f"{normalized_url(result.url)}|{normalize_domain(result.domain)}"
            for result in deduped_results
        }

        ranked: list[RankedResult] = []
        consumed_keys: set[str] = set()
        for query, position, total, result in candidates:
            key = f"{normalized_url(result.url)}|{normalize_domain(result.domain)}"
            if key not in kept_keys or key in consumed_keys:
                continue
            consumed_keys.add(key)
            domain = normalize_domain(result.domain) or extract_domain(result.url)
            official = is_official_domain(domain, self._trusted_domains)
            resource_type = classify_resource_type(
                result.title,
                result.url,
                domain,
                result.snippet,
                is_official=official,
            )
            score, _signals = score_result(
                result,
                position=position,
                total=total,
                topic_words=topic_word_set,
                is_official=official,
                resource_type=resource_type,
                query_occurrences=occurrences.get(key, 1),
            )
            ranked.append(
                RankedResult(
                    result=result,
                    score=score,
                    query_occurrences=occurrences.get(key, 1),
                )
            )

        return [
            self._to_resource(item, topic=topic)
            for item in sort_by_score(ranked)[:count]
        ]

    def _to_resource(
        self, item: RankedResult, *, topic: str
    ) -> LearningResource:
        result = item.result
        domain = normalize_domain(result.domain) or extract_domain(result.url)
        official = is_official_domain(domain, self._trusted_domains)
        return LearningResource(
            title=result.title,
            url=result.url,
            domain=domain,
            description=result.snippet,
            resource_type=classify_resource_type(
                result.title,
                result.url,
                domain,
                result.snippet,
                is_official=official,
            ),
            is_official=official,
            difficulty=detect_difficulty(result.title, result.url, result.snippet),
            relevance_score=item.score,
            source=result.source,
            retrieved_at=result.retrieved_at,
            topic=topic,
        )