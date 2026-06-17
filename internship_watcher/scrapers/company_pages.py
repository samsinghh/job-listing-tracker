"""Stubs for companies that need bespoke scraping.

Google, Meta, NVIDIA (Workday), and Jane Street render listings client-side
and/or sit behind undocumented or anti-bot-protected endpoints. Rather than
ship something fragile and silently broken, the `stub` scraper documents the
limitation and returns no listings, surfacing the reason at runtime.

To enable one of these, implement a real scraper (e.g. a Workday adapter for
NVIDIA, or a Playwright-backed scraper for the JS sites), register it in
`scrapers/__init__.py`, and point the company's `scraper` field at it.
"""

from __future__ import annotations

import logging

from ..config import CompanyConfig
from ..models import RawListing
from .base import Scraper

log = logging.getLogger(__name__)


class StubScraper(Scraper):
    name = "stub"

    def fetch(self, company: CompanyConfig) -> list[RawListing]:
        reason = company.params.get("reason", "not yet implemented")
        log.warning(
            "Skipping %s: scraper not implemented. %s",
            company.name,
            " ".join(str(reason).split()),
        )
        return []
