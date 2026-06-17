"""Greenhouse job-board scraper.

Uses the public board API:
    https://boards-api.greenhouse.io/v1/boards/{board}/jobs

Config params:
    board: the board token (e.g. "anthropic", "databricks", "stripe").
"""

from __future__ import annotations

from ..config import CompanyConfig
from ..models import RawListing
from .base import Scraper, ScraperError, get_json

API = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"


class GreenhouseScraper(Scraper):
    name = "greenhouse"

    def fetch(self, company: CompanyConfig) -> list[RawListing]:
        board = company.params.get("board")
        if not board:
            raise ScraperError(f"{company.name}: greenhouse scraper requires 'board'")

        data = get_json(API.format(board=board))
        jobs = data.get("jobs", []) if isinstance(data, dict) else []

        listings: list[RawListing] = []
        for job in jobs:
            title = (job.get("title") or "").strip()
            url = job.get("absolute_url") or ""
            if not title or not url:
                continue
            location = (job.get("location") or {}).get("name")
            listings.append(
                RawListing(
                    company=company.name,
                    title=title,
                    url=url,
                    location=location,
                    source=self.name,
                    external_id=str(job.get("id")) if job.get("id") else None,
                )
            )
        return listings
