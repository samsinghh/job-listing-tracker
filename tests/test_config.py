import pytest

from internship_watcher.config import load_config

BASE = """
keywords:
  match: [intern]
  exclude: [senior]
companies:
  - name: Anthropic
    scraper: greenhouse
    board: anthropic
"""


def _write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(text)
    return p


class TestEmailConfig:
    def test_absent_email_is_none(self, tmp_path):
        cfg = load_config(_write(tmp_path, BASE))
        assert cfg.email is None

    def test_parsed_with_defaults(self, tmp_path):
        text = BASE + "email:\n  enabled: true\n  to: me@x.com\n"
        cfg = load_config(_write(tmp_path, text))
        assert cfg.email.enabled is True
        assert cfg.email.to == ["me@x.com"]  # scalar coerced to list
        assert cfg.email.smtp_host == "smtp.gmail.com"
        assert cfg.email.smtp_port == 587
        assert cfg.email.sender is None

    def test_enabled_without_recipient_raises(self, tmp_path):
        text = BASE + "email:\n  enabled: true\n"
        with pytest.raises(ValueError, match="email.to is empty"):
            load_config(_write(tmp_path, text))


class TestCompanyParsing:
    def test_company_params_captured(self, tmp_path):
        cfg = load_config(_write(tmp_path, BASE))
        assert cfg.companies[0].scraper == "greenhouse"
        assert cfg.companies[0].params == {"board": "anthropic"}
