"""Ashby job-board scraper.

Uses the public posting API:
    https://api.ashbyhq.com/posting-api/job-board/{org}

Config params:
    org: the Ashby org slug (e.g. "openai").
"""

from __future__ import annotations

from ..config import CompanyConfig
from ..models import RawListing
from .base import Scraper, ScraperError, get_json

API = "https://api.ashbyhq.com/posting-api/job-board/{org}"


class AshbyScraper(Scraper):
    name = "ashby"

    def fetch(self, company: CompanyConfig) -> list[RawListing]:
        org = company.params.get("org")
        if not org:
            raise ScraperError(f"{company.name}: ashby scraper requires 'org'")

        data = get_json(API.format(org=org))
        jobs = data.get("jobs", []) if isinstance(data, dict) else []

        listings: list[RawListing] = []
        for job in jobs:
            if job.get("isListed") is False:
                continue
            title = (job.get("title") or "").strip()
            url = job.get("jobUrl") or job.get("applyUrl") or ""
            if not title or not url:
                continue
            listings.append(
                RawListing(
                    company=company.name,
                    title=title,
                    url=url,
                    location=job.get("location"),
                    source=self.name,
                    external_id=str(job.get("id")) if job.get("id") else None,
                )
            )
        return listings
