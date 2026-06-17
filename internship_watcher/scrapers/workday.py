"""Workday scraper (used for NVIDIA).

Workday tenants expose a JSON "CXS" search API:

    POST https://{host}/wday/cxs/{tenant}/{site}/jobs
    body: {"appliedFacets": {}, "limit": 20, "offset": N, "searchText": "..."}

Results are paginated; Workday caps `limit` at 20 (larger values return an
empty response), so we page through `offset` until `total` is reached.

Config params:
    host:        e.g. "nvidia.wd5.myworkdayjobs.com"   (required)
    tenant:      e.g. "nvidia"                          (required)
    site:        e.g. "NVIDIAExternalCareerSite"        (required)
    search_text: server-side full-text prefilter (optional, recommended).
                 Large Workday tenants have thousands of postings; without a
                 prefilter we would page through all of them (hundreds of
                 requests). "intern" narrows the fetch to a superset of
                 internship roles; the CLI's title keyword filter then applies
                 precisely on top.
    max_results: safety cap on total postings fetched (default 2000).

Limitation: a 2027 internship whose title matches a keyword but whose posting
text never contains the `search_text` term could be missed by the prefilter.
For internship monitoring, "intern" is well aligned and this is rarely an issue.
"""

from __future__ import annotations

import logging

from ..config import CompanyConfig
from ..models import RawListing
from .base import Scraper, ScraperError, get_json

log = logging.getLogger(__name__)

PAGE_SIZE = 20  # Workday hard cap
DEFAULT_MAX_RESULTS = 2000


class WorkdayScraper(Scraper):
    name = "workday"

    def fetch(self, company: CompanyConfig) -> list[RawListing]:
        host = company.params.get("host")
        tenant = company.params.get("tenant")
        site = company.params.get("site")
        if not (host and tenant and site):
            raise ScraperError(
                f"{company.name}: workday scraper requires 'host', 'tenant', 'site'"
            )
        search_text = company.params.get("search_text", "") or ""
        max_results = int(company.params.get("max_results", DEFAULT_MAX_RESULTS))

        cxs_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        base_url = f"https://{host}/{site}"  # externalPath is appended to this

        listings: list[RawListing] = []
        offset = 0
        total: int | None = None

        while offset < max_results:
            data = get_json(
                cxs_url,
                method="POST",
                json={
                    "appliedFacets": {},
                    "limit": PAGE_SIZE,
                    "offset": offset,
                    "searchText": search_text,
                },
                headers={"Content-Type": "application/json"},
            )
            if not isinstance(data, dict):
                raise ScraperError(f"{company.name}: unexpected Workday response shape")

            if total is None:
                total = data.get("total")

            postings = data.get("jobPostings") or []
            if not postings:
                break

            for p in postings:
                parsed = self._parse_posting(p, base_url, company.name)
                if parsed:
                    listings.append(parsed)

            offset += PAGE_SIZE
            if total is not None and offset >= total:
                break

        if total is not None and total > max_results:
            log.warning(
                "%s: capped at %d of %d Workday postings (raise max_results to fetch more)",
                company.name,
                max_results,
                total,
            )

        return listings

    @staticmethod
    def _parse_posting(
        posting: dict, base_url: str, company: str
    ) -> RawListing | None:
        """Convert one Workday jobPosting dict into a RawListing.

        Pure (no I/O) so it can be unit-tested against a sample payload.
        Returns None if the posting lacks a usable title or path.
        """
        title = (posting.get("title") or "").strip()
        external_path = posting.get("externalPath") or ""
        if not title or not external_path:
            return None

        url = base_url.rstrip("/") + external_path
        bullets = posting.get("bulletFields") or []
        external_id = bullets[0] if bullets else external_path

        return RawListing(
            company=company,
            title=title,
            url=url,
            location=posting.get("locationsText"),
            source=WorkdayScraper.name,
            external_id=str(external_id),
        )
