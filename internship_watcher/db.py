"""SQLite persistence and new-listing detection."""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone

from .matching import normalize_title, normalize_url
from .models import RawListing, StoredListing

_SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    dedup_key        TEXT PRIMARY KEY,
    company          TEXT NOT NULL,
    title            TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    url              TEXT NOT NULL,
    location         TEXT,
    source           TEXT,
    external_id      TEXT,
    first_seen       TEXT NOT NULL,
    last_seen        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_listings_company ON listings(company);
CREATE INDEX IF NOT EXISTS idx_listings_first_seen ON listings(first_seen);
"""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def dedup_key(
    company: str, title: str, url: str, external_id: str | None = None
) -> str:
    """Stable identity for a listing: company + normalized title + URL/id.

    Cosmetic title/URL variations (case, punctuation, tracking query params)
    dedupe to the same key. When the scraper supplies a stable ATS `external_id`
    it is used in place of the URL — necessary because some boards (e.g.
    Greenhouse) put the job id in the query string, which `normalize_url` drops,
    so distinct roles sharing a title+path would otherwise collide.
    """
    identity = external_id.strip() if external_id else normalize_url(url)
    basis = "|".join(
        (
            company.strip().lower(),
            normalize_title(title),
            identity,
        )
    )
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()


def connect(path: str) -> sqlite3.Connection:
    """Open (creating if needed) the SQLite database and ensure the schema."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _row_to_listing(row: sqlite3.Row) -> StoredListing:
    return StoredListing(
        dedup_key=row["dedup_key"],
        company=row["company"],
        title=row["title"],
        normalized_title=row["normalized_title"],
        url=row["url"],
        location=row["location"],
        source=row["source"],
        external_id=row["external_id"],
        first_seen=row["first_seen"],
        last_seen=row["last_seen"],
    )


def upsert_listings(
    conn: sqlite3.Connection,
    listings: list[RawListing],
    now: str | None = None,
) -> list[StoredListing]:
    """Insert listings, returning only those new to the database.

    For each listing: `INSERT OR IGNORE` by dedup_key. If the row was inserted
    (rowcount == 1) it is new this run; otherwise we refresh `last_seen` on the
    existing row. `now` is injectable for deterministic tests.
    """
    ts = now or _utcnow()
    new: list[StoredListing] = []

    for item in listings:
        key = dedup_key(item.company, item.title, item.url, item.external_id)
        norm_title = normalize_title(item.title)
        cur = conn.execute(
            """
            INSERT OR IGNORE INTO listings
                (dedup_key, company, title, normalized_title, url, location,
                 source, external_id, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                key,
                item.company,
                item.title,
                norm_title,
                item.url,
                item.location,
                item.source,
                item.external_id,
                ts,
                ts,
            ),
        )
        if cur.rowcount == 1:
            new.append(
                StoredListing(
                    dedup_key=key,
                    company=item.company,
                    title=item.title,
                    normalized_title=norm_title,
                    url=item.url,
                    location=item.location,
                    source=item.source,
                    external_id=item.external_id,
                    first_seen=ts,
                    last_seen=ts,
                )
            )
        else:
            conn.execute(
                "UPDATE listings SET last_seen = ? WHERE dedup_key = ?",
                (ts, key),
            )

    conn.commit()
    return new


def list_listings(
    conn: sqlite3.Connection,
    company: str | None = None,
    limit: int | None = None,
) -> list[StoredListing]:
    """Return stored listings, most recently first-seen first."""
    sql = "SELECT * FROM listings"
    params: list[object] = []
    if company:
        sql += " WHERE company = ?"
        params.append(company)
    sql += " ORDER BY first_seen DESC, company ASC"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return [_row_to_listing(r) for r in conn.execute(sql, params)]


def count_by_company(conn: sqlite3.Connection) -> dict[str, int]:
    """Return a {company: stored listing count} mapping."""
    rows = conn.execute(
        "SELECT company, COUNT(*) AS n FROM listings GROUP BY company"
    )
    return {r["company"]: r["n"] for r in rows}
