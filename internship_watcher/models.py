"""Core data structures shared across the package."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawListing:
    """A job listing as returned by a scraper, before persistence.

    Scrapers are responsible only for extracting these fields. Normalization
    and dedup-key computation happen in `db`/`matching`, so scrapers stay
    simple and consistent.
    """

    company: str
    title: str
    url: str
    location: str | None = None
    source: str = ""  # which scraper produced it, e.g. "greenhouse"
    external_id: str | None = None  # ATS-native id, for debugging/traceability


@dataclass(frozen=True)
class StoredListing:
    """A listing as persisted in SQLite."""

    dedup_key: str
    company: str
    title: str
    normalized_title: str
    url: str
    location: str | None
    source: str
    external_id: str | None
    first_seen: str  # ISO-8601 UTC
    last_seen: str  # ISO-8601 UTC
