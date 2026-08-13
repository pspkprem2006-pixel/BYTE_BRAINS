"""Transparent relevance ranking for learning resources.

The score is a weighted sum of small, explainable signals:

- provider relevance, when the search provider supplies one, otherwise a
  position-based score (0.6 for the first result, gently decreasing)
- +0.20 for official sources
- +0.15 when the topic matches a word in the title
- +0.05 for "hands-on" resource types (practice, official docs, tutorial)
- +0.05 when the same resource was found through more than one query variant
  (evidence it is stable and on-topic)

Scores are clamped to [0, 1] and rounded to two decimals. No ML, no
tunable black box: the contribution of each signal is documented above.
"""

import re
from dataclasses import dataclass, field

from app.schemas.learning_resources import ResourceType

from app.services.search.models import SearchResult

OFFICIAL_BONUS = 0.20
TOPIC_TITLE_BONUS = 0.15
TYPE_BONUS = {
    ResourceType.official_docs: 0.05,
    ResourceType.practice: 0.05,
    ResourceType.tutorial: 0.05,
    ResourceType.reference: 0.03,
}
MULTI_QUERY_BONUS = 0.05

_FIRST_POSITION_SCORE = 0.60
_POSITION_STEP = 0.05
_POSITION_FLOOR = 0.30


@dataclass
class RankedResult:
    """A search result plus the evidence used to rank it."""

    result: SearchResult
    score: float
    query_occurrences: int = 1
    signals: list[str] = field(default_factory=list)


def _position_relevance(index: int, total: int) -> float:
    """Position-based relevance when the provider gives no score.

    The first position starts at 0.60 and loses 0.05 per position until the
    floor. Kept gentle so that stronger signals (official source, topic
    match) can outrank a lucky first position.
    """
    return max(_POSITION_FLOOR, _FIRST_POSITION_SCORE - index * _POSITION_STEP)


def _title_matches_topic(title: str, topic_words: frozenset[str]) -> bool:
    """True when any significant topic word appears in the title."""
    if not topic_words:
        return False
    title_lower = title.lower()
    return any(
        re.search(rf"\b{re.escape(word)}\b", title_lower) for word in topic_words
    )


def score_result(
    result: SearchResult,
    *,
    position: int,
    total: int,
    topic_words: frozenset[str],
    is_official: bool,
    resource_type: ResourceType,
    query_occurrences: int,
) -> tuple[float, list[str]]:
    """Compute the relevance score and the signals behind it."""
    signals: list[str] = []
    if result.relevance_score is not None:
        score = float(result.relevance_score)
    else:
        score = _position_relevance(position, total)

    if is_official:
        score += OFFICIAL_BONUS
        signals.append("official")
    if _title_matches_topic(result.title, topic_words):
        score += TOPIC_TITLE_BONUS
        signals.append("title-matches-topic")
    type_bonus = TYPE_BONUS.get(resource_type, 0.0)
    if type_bonus:
        score += type_bonus
        signals.append(resource_type.value)
    if query_occurrences > 1:
        score += MULTI_QUERY_BONUS
        signals.append("found-in-multiple-queries")

    return round(max(0.0, min(1.0, score)), 2), signals


def sort_by_score(ranked: list[RankedResult]) -> list[RankedResult]:
    """Stable sort: score desc, then query-occurrence evidence, then title."""
    return sorted(
        ranked,
        key=lambda item: (
            -item.score,
            -item.query_occurrences,
            item.result.title.lower(),
        ),
    )