"""Title/URL normalization and keyword matching.

This module is deliberately pure (no I/O) so it is easy to unit-test.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

# Collapses any run of non-alphanumeric characters into a single space.
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_title(title: str) -> str:
    """Normalize a job title for stable comparison and matching.

    Lowercases, replaces punctuation with spaces, and collapses whitespace.

        "Software Engineer Intern, Summer 2027 (Remote)"
        -> "software engineer intern summer 2027 remote"
    """
    if not title:
        return ""
    lowered = title.lower()
    collapsed = _NON_ALNUM.sub(" ", lowered)
    return collapsed.strip()


def normalize_url(url: str) -> str:
    """Normalize a URL so trivial variations dedupe to the same key.

    Lowercases the scheme/host, drops query string and fragment (ATS apply
    URLs append tracking params), and strips a trailing slash from the path.
    """
    if not url:
        return ""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    return urlunsplit((scheme, netloc, path, "", ""))


def _keyword_pattern(keyword: str) -> re.Pattern[str] | None:
    """Build a word-boundary regex for a (possibly multi-word) keyword.

    The keyword is normalized the same way as titles, so phrase keywords like
    "software engineer intern" match regardless of the original punctuation.
    Returns None for keywords that normalize to empty.
    """
    norm = normalize_title(keyword)
    if not norm:
        return None
    return re.compile(rf"\b{re.escape(norm)}\b")


def matches(title: str, match_keywords: list[str], exclude_keywords: list[str]) -> bool:
    """Return True if `title` matches the inclusion rules.

    A title matches when it contains at least one `match` keyword and none of
    the `exclude` keywords. Matching is word-boundary aware on the normalized
    title, so "Internal Tools Engineer" does NOT match the keyword "intern".
    """
    norm_title = normalize_title(title)
    if not norm_title:
        return False

    for kw in exclude_keywords:
        pat = _keyword_pattern(kw)
        if pat and pat.search(norm_title):
            return False

    for kw in match_keywords:
        pat = _keyword_pattern(kw)
        if pat and pat.search(norm_title):
            return True

    return False
