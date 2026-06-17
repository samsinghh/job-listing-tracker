import pytest

from internship_watcher import db
from internship_watcher.models import RawListing


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    yield c
    c.close()


def _listing(title="SWE Intern", url="https://x.com/jobs/1", company="Anthropic"):
    return RawListing(
        company=company, title=title, url=url, location="SF", source="test"
    )


class TestUpsert:
    def test_first_insert_is_new(self, conn):
        new = db.upsert_listings(conn, [_listing()], now="2026-06-16T00:00:00Z")
        assert len(new) == 1
        assert new[0].company == "Anthropic"
        assert new[0].normalized_title == "swe intern"

    def test_reinsert_same_listing_is_not_new(self, conn):
        db.upsert_listings(conn, [_listing()], now="2026-06-16T00:00:00Z")
        new = db.upsert_listings(conn, [_listing()], now="2026-06-17T00:00:00Z")
        assert new == []
        assert len(db.list_listings(conn)) == 1

    def test_reinsert_updates_last_seen_not_first_seen(self, conn):
        db.upsert_listings(conn, [_listing()], now="2026-06-16T00:00:00Z")
        db.upsert_listings(conn, [_listing()], now="2026-06-17T00:00:00Z")
        row = db.list_listings(conn)[0]
        assert row.first_seen == "2026-06-16T00:00:00Z"
        assert row.last_seen == "2026-06-17T00:00:00Z"

    def test_cosmetic_variation_dedupes(self, conn):
        db.upsert_listings(conn, [_listing()], now="2026-06-16T00:00:00Z")
        variant = _listing(title="SWE  Intern!", url="https://x.com/jobs/1?utm=x")
        new = db.upsert_listings(conn, [variant], now="2026-06-17T00:00:00Z")
        assert new == []
        assert len(db.list_listings(conn)) == 1

    def test_new_listing_detected_across_runs(self, conn):
        db.upsert_listings(conn, [_listing()], now="2026-06-16T00:00:00Z")
        second = _listing(title="ML Intern", url="https://x.com/jobs/2")
        new = db.upsert_listings(
            conn, [_listing(), second], now="2026-06-17T00:00:00Z"
        )
        assert len(new) == 1
        assert new[0].title == "ML Intern"
        assert len(db.list_listings(conn)) == 2


class TestQueries:
    def test_filter_by_company_and_counts(self, conn):
        db.upsert_listings(
            conn,
            [
                _listing(company="Anthropic"),
                _listing(title="ML Intern", url="https://x.com/jobs/2", company="OpenAI"),
            ],
            now="2026-06-16T00:00:00Z",
        )
        assert db.count_by_company(conn) == {"Anthropic": 1, "OpenAI": 1}
        assert len(db.list_listings(conn, company="OpenAI")) == 1
