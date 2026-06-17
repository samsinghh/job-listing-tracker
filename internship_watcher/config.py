"""Loading and validation of config.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class CompanyConfig:
    name: str
    scraper: str
    # Scraper-specific parameters (board, org, url, reason, ...).
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EmailConfig:
    enabled: bool
    to: list[str]
    sender: str | None  # None -> fall back to the SMTP login user
    smtp_host: str
    smtp_port: int


@dataclass(frozen=True)
class Config:
    match_keywords: list[str]
    exclude_keywords: list[str]
    companies: list[CompanyConfig]
    email: EmailConfig | None = None


DEFAULT_CONFIG_PATH = "config.yaml"


def _parse_email(raw: dict | None) -> EmailConfig | None:
    if not raw:
        return None
    to = raw.get("to")
    to_list = [to] if isinstance(to, str) else [str(t) for t in (to or [])]
    cfg = EmailConfig(
        enabled=bool(raw.get("enabled", False)),
        to=to_list,
        sender=raw.get("from"),
        smtp_host=str(raw.get("smtp_host", "smtp.gmail.com")),
        smtp_port=int(raw.get("smtp_port", 587)),
    )
    if cfg.enabled and not cfg.to:
        raise ValueError("config: email.enabled is true but email.to is empty")
    return cfg


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Config:
    """Parse and validate the YAML config file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")

    data = yaml.safe_load(p.read_text()) or {}

    keywords = data.get("keywords") or {}
    match_keywords = [str(k) for k in (keywords.get("match") or [])]
    exclude_keywords = [str(k) for k in (keywords.get("exclude") or [])]
    if not match_keywords:
        raise ValueError("config: keywords.match must contain at least one keyword")

    companies: list[CompanyConfig] = []
    for i, raw in enumerate(data.get("companies") or []):
        if not isinstance(raw, dict):
            raise ValueError(f"config: companies[{i}] must be a mapping")
        name = raw.get("name")
        scraper = raw.get("scraper")
        if not name or not scraper:
            raise ValueError(
                f"config: companies[{i}] requires 'name' and 'scraper'"
            )
        params = {k: v for k, v in raw.items() if k not in ("name", "scraper")}
        companies.append(CompanyConfig(name=name, scraper=scraper, params=params))

    if not companies:
        raise ValueError("config: at least one company is required")

    return Config(
        match_keywords=match_keywords,
        exclude_keywords=exclude_keywords,
        companies=companies,
        email=_parse_email(data.get("email")),
    )
