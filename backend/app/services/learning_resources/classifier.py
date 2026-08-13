"""Conservative classification of web search results into learning resources.

Everything here is heuristic, keyword and domain based. When a type or
difficulty cannot be determined with reasonable confidence, the result is
labeled "other" / None instead of guessing.
"""

import re
from urllib.parse import urlparse

from app.schemas.learning_resources import ResourceType

_VIDEO_DOMAINS = frozenset({"youtube.com", "youtu.be", "vimeo.com", "dailymotion.com"})
_PRACTICE_DOMAINS = frozenset(
    {
        "leetcode.com",
        "hackerrank.com",
        "codewars.com",
        "exercism.org",
        "codingame.com",
        "edabit.com",
    }
)
_COURSE_DOMAINS = frozenset(
    {"coursera.org", "udemy.com", "edx.org", "pluralsight.com", "udacity.com"}
)
_BLOG_DOMAINS = frozenset(
    {
        "medium.com",
        "dev.to",
        "towardsdatascience.com",
        "freecodecamp.org",
        "blog.logrocket.com",
        "css-tricks.com",
        "smashingmagazine.com",
    }
)

_VIDEO_HINTS = re.compile(r"\b(video|watch)\b|youtu\.be/|v=")
_DOC_HINTS = re.compile(
    r"\b(docs|documentation|reference|manual|api reference)\b|/docs/|/doc/"
)
_TUTORIAL_HINTS = re.compile(
    r"\b(tutorial|guide|getting started|get started|how to|learn|cookbook|"
    r"crash course|walkthrough)\b",
    re.IGNORECASE,
)
_PRACTICE_HINTS = re.compile(
    r"\b(exercise|exercises|practice|problems|katas|challenges|drills|quiz)\b",
    re.IGNORECASE,
)
_COURSE_HINTS = re.compile(r"\b(course|mooc|bootcamp)\b", re.IGNORECASE)
_REFERENCE_HINTS = re.compile(
    r"\b(cheat ?sheet|glossary|api|man page|manpages)\b", re.IGNORECASE
)
_ARTICLE_HINTS = re.compile(
    r"\b(blog|article|post|explained|deep dive|under the hood)\b", re.IGNORECASE
)

_BEGINNER_HINTS = re.compile(
    r"\b(beginner|beginners|intro|introduction|basics|getting started|"
    r"get started|start here|crash course|for dummies|absolute beginner)\b",
    re.IGNORECASE,
)
_ADVANCED_HINTS = re.compile(
    r"\b(advanced|expert|internals|deep dive|performance tuning|in-depth|"
    r"under the hood|pro tip)\b",
    re.IGNORECASE,
)


def normalize_domain(domain: str) -> str:
    """Lowercase a host and strip a leading ``www.`` prefix.

    ``WWW.Example.COM`` -> ``example.com``. This is the canonical form used
    for deduplication and official-source matching.
    """
    host = (domain or "").strip().lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def is_official_domain(domain: str, trusted_domains: frozenset[str]) -> bool:
    """True when the domain is (or is a subdomain of) a trusted domain.

    Matching is conservative: ``docs.postgresql.org`` counts as
    postgresql.org, but ``postgresql.org.evil.example`` does not.
    """
    host = normalize_domain(domain)
    if not host:
        return False
    for trusted in trusted_domains:
        if host == trusted or host.endswith("." + trusted):
            return True
    return False


def classify_resource_type(
    title: str,
    url: str,
    domain: str,
    snippet: str,
    *,
    is_official: bool,
) -> ResourceType:
    """Assign one of the supported resource types.

    Checks run from the most confident signal to the least: hosting domains
    first (youtube is always a video), then official documentation, then
    keyword hints. Anything that cannot be recognized stays "other".
    """
    domain = normalize_domain(domain)
    title_lower = title.lower()
    url_lower = url.lower()
    # Hyphenated slugs read as words: "sql-cheat-sheet" -> "sql cheat sheet".
    url_text = url_lower.replace("-", " ")
    text = f"{title} {snippet} {url_text}".lower()

    if domain in _VIDEO_DOMAINS or _VIDEO_HINTS.search(url_lower):
        return ResourceType.video
    if domain in _PRACTICE_DOMAINS or _PRACTICE_HINTS.search(text):
        return ResourceType.practice
    if domain in _COURSE_DOMAINS or _COURSE_HINTS.search(text):
        return ResourceType.course
    if is_official and (
        _DOC_HINTS.search(url_lower) or _DOC_HINTS.search(title_lower)
    ):
        return ResourceType.official_docs
    if _TUTORIAL_HINTS.search(text):
        return ResourceType.tutorial
    if _DOC_HINTS.search(url_lower) or _DOC_HINTS.search(text) or _REFERENCE_HINTS.search(text):
        return ResourceType.reference
    if domain in _BLOG_DOMAINS or _ARTICLE_HINTS.search(text):
        return ResourceType.article
    return ResourceType.other


def detect_difficulty(title: str, url: str, snippet: str) -> str | None:
    """Return a difficulty label only when it can be detected confidently.

    Beginner and advanced hints are recognized; "intermediate" is never
    guessed, so a None difficulty means "could not be determined".
    """
    text = f"{title} {url} {snippet}".lower()
    advanced = bool(_ADVANCED_HINTS.search(text))
    beginner = bool(_BEGINNER_HINTS.search(text))
    if beginner and not advanced:
        return "beginner"
    if advanced and not beginner:
        return "advanced"
    return None


def extract_domain(url: str) -> str:
    """Extract the lowercased host from a URL, or "" for invalid URLs."""
    try:
        host = urlparse(url).netloc
    except ValueError:
        return ""
    return normalize_domain(host)