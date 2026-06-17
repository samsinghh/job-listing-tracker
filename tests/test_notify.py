import pytest

from internship_watcher import notify
from internship_watcher.config import EmailConfig
from internship_watcher.models import StoredListing


def _listing(company="Stripe", title="SWE Intern", url="https://x.com/jobs/1"):
    return StoredListing(
        dedup_key="k",
        company=company,
        title=title,
        normalized_title="swe intern",
        url=url,
        location="SF",
        source="test",
        external_id="1",
        first_seen="2026-06-16T00:00:00Z",
        last_seen="2026-06-16T00:00:00Z",
    )


class TestBuildMessage:
    def test_subject_counts_listings(self):
        msg = notify.build_message(["me@x.com"], "me@x.com", [_listing(), _listing()])
        assert "2 new listing(s)" in msg["Subject"]

    def test_headers_and_body(self):
        msg = notify.build_message(
            ["a@x.com", "b@x.com"], "sender@x.com", [_listing()]
        )
        assert msg["To"] == "a@x.com, b@x.com"
        assert msg["From"] == "sender@x.com"
        body = msg.get_content()
        assert "[Stripe] SWE Intern" in body
        assert "https://x.com/jobs/1" in body


class TestSendNewListings:
    EMAIL_CFG = EmailConfig(
        enabled=True,
        to=["me@x.com"],
        sender=None,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
    )

    def test_no_listings_is_noop(self, monkeypatch):
        # Should not even look at credentials when there is nothing to send.
        monkeypatch.delenv(notify.ENV_USER, raising=False)
        monkeypatch.delenv(notify.ENV_PASSWORD, raising=False)
        assert notify.send_new_listings(self.EMAIL_CFG, []) is False

    def test_missing_credentials_raises(self, monkeypatch):
        monkeypatch.delenv(notify.ENV_USER, raising=False)
        monkeypatch.delenv(notify.ENV_PASSWORD, raising=False)
        with pytest.raises(notify.NotifyError, match="missing credentials"):
            notify.send_new_listings(self.EMAIL_CFG, [_listing()])


class TestRecipients:
    def test_falls_back_to_config(self, monkeypatch):
        monkeypatch.delenv(notify.ENV_TO, raising=False)
        cfg = EmailConfig(True, ["cfg@x.com"], None, "smtp.gmail.com", 587)
        assert notify._recipients(cfg) == ["cfg@x.com"]

    def test_env_overrides_config_and_splits(self, monkeypatch):
        monkeypatch.setenv(notify.ENV_TO, "a@x.com, b@x.com")
        cfg = EmailConfig(True, ["cfg@x.com"], None, "smtp.gmail.com", 587)
        assert notify._recipients(cfg) == ["a@x.com", "b@x.com"]
