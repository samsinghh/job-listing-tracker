"""Scraper interface and shared HTTP helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from ..config import CompanyConfig
from ..models import RawListing

# A descriptive UA; some ATS endpoints reject empty/blank user agents.
USER_AGENT = "internship-watcher/0.1 (+https://github.com/local/internship-watcher)"
DEFAULT_TIMEOUT = 20


class ScraperError(Exception):
    """Raised when a scraper cannot retrieve or parse listings.

    The CLI catches this per-company so one broken source does not abort the
    whole run.
    """


class Scraper(ABC):
    """Base class for all scrapers.

    A scraper takes a `CompanyConfig` and returns every listing it can find;
    keyword filtering is applied later by the caller, so scrapers should NOT
    pre-filter on title.
    """

    name: str = "base"

    @abstractmethod
    def fetch(self, company: CompanyConfig) -> list[RawListing]:
        ...


def get_json(url: str, *, method: str = "GET", **kwargs) -> dict | list:
    """Fetch and parse JSON, raising ScraperError on any failure."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    headers.update(kwargs.pop("headers", {}) or {})
    try:
        resp = requests.request(
            method, url, headers=headers, timeout=DEFAULT_TIMEOUT, **kwargs
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise ScraperError(f"request failed for {url}: {e}") from e
    except ValueError as e:
        raise ScraperError(f"invalid JSON from {url}: {e}") from e
