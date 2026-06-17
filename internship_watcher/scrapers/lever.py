"""Lever job-board scraper.

Uses the public postings API:
    https://api.lever.co/v0/postings/{company}?mode=json

None of the initial target companies use Lever, but many startups do, so this
adapter is provided for extensibility. Config params:
    company: the Lever account slug.
"""

from __future__ import annotations

from ..config import CompanyConfig
from ..models import RawListing
from .base import Scraper, ScraperError, get_json

API = "https://api.lever.co/v0/postings/{slug}?mode=json"


class LeverScraper(Scraper):
    name = "lever"

    def fetch(self, company: CompanyConfig) -> list[RawListing]:
        slug = company.params.get("company") or company.params.get("slug")
        if not slug:
            raise ScraperError(f"{company.name}: lever scraper requires 'company'")

        data = get_json(API.format(slug=slug))
        if not isinstance(data, list):
            raise ScraperError(f"{company.name}: unexpected Lever response shape")

        listings: list[RawListing] = []
        for job in data:
            title = (job.get("text") or "").strip()
            url = job.get("hostedUrl") or job.get("applyUrl") or ""
            if not title or not url:
                continue
            location = (job.get("categories") or {}).get("location")
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
