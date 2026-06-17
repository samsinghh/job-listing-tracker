"""Scraper registry.

Maps the `scraper` field in config.yaml to a scraper instance. To add a new
backend, implement a `Scraper` subclass and register it here.
"""

from __future__ import annotations

from .ashby import AshbyScraper
from .base import Scraper, ScraperError
from .company_pages import StubScraper
from .greenhouse import GreenhouseScraper
from .lever import LeverScraper
from .workday import WorkdayScraper

_REGISTRY: dict[str, Scraper] = {
    GreenhouseScraper.name: GreenhouseScraper(),
    LeverScraper.name: LeverScraper(),
    AshbyScraper.name: AshbyScraper(),
    WorkdayScraper.name: WorkdayScraper(),
    StubScraper.name: StubScraper(),
}


def get_scraper(name: str) -> Scraper:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ScraperError(
            f"unknown scraper '{name}'; known: {sorted(_REGISTRY)}"
        ) from None


def available_scrapers() -> list[str]:
    return sorted(_REGISTRY)


__all__ = ["get_scraper", "available_scrapers", "Scraper", "ScraperError"]
