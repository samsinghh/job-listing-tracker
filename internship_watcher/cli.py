"""Command-line interface."""

from __future__ import annotations

import argparse
import logging
import sys

from . import db, notify
from .config import Config, load_config
from .matching import matches
from .models import RawListing, StoredListing
from .scrapers import ScraperError, get_scraper

DEFAULT_DB_PATH = "internships.db"


def _collect_matches(config: Config) -> list[RawListing]:
    """Run every configured scraper and return listings that match keywords."""
    collected: list[RawListing] = []
    for company in config.companies:
        try:
            scraper = get_scraper(company.scraper)
            raw = scraper.fetch(company)
        except ScraperError as e:
            print(f"  ! {company.name}: {e}", file=sys.stderr)
            continue

        kept = [
            r
            for r in raw
            if matches(r.title, config.match_keywords, config.exclude_keywords)
        ]
        print(f"  - {company.name}: {len(kept)} match / {len(raw)} fetched")
        collected.extend(kept)
    return collected


def _print_listing(listing: StoredListing, prefix: str = "") -> None:
    loc = f" — {listing.location}" if listing.location else ""
    print(f"{prefix}[{listing.company}] {listing.title}{loc}")
    print(f"{prefix}    {listing.url}")


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    conn = db.connect(args.db)

    print("Checking companies...")
    matched = _collect_matches(config)
    new = db.upsert_listings(conn, matched)

    print()
    if new:
        print(f"=== {len(new)} NEW matching listing(s) ===")
        for listing in new:
            _print_listing(listing, prefix="  ")
    else:
        print("No new matching listings since the last run.")

    _maybe_send_email(config, new, args)

    print(f"\nTotal matching listings tracked: {len(db.list_listings(conn))}")
    return 0


def _maybe_send_email(
    config: Config, new: list[StoredListing], args: argparse.Namespace
) -> None:
    """Email new listings when email is enabled and there is something to send."""
    if getattr(args, "no_email", False):
        return
    email_cfg = config.email
    if not (email_cfg and email_cfg.enabled) or not new:
        return
    try:
        if notify.send_new_listings(email_cfg, new):
            print(f"Emailed {len(new)} new listing(s).")
    except notify.NotifyError as e:
        print(f"  ! email not sent: {e}", file=sys.stderr)


def cmd_list(args: argparse.Namespace) -> int:
    conn = db.connect(args.db)
    listings = db.list_listings(conn, company=args.company, limit=args.limit)
    if not listings:
        print("No listings stored yet. Run `internship_watcher run` first.")
        return 0
    print(f"{len(listings)} stored listing(s):")
    for listing in listings:
        _print_listing(listing, prefix="  ")
    return 0


def cmd_companies(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    conn = db.connect(args.db)
    counts = db.count_by_company(conn)
    print(f"{len(config.companies)} configured compan(ies):")
    for c in config.companies:
        status = "stub" if c.scraper == "stub" else c.scraper
        n = counts.get(c.name, 0)
        print(f"  - {c.name:<14} scraper={status:<11} tracked={n}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="internship_watcher",
        description="Monitor company careers pages for 2027 summer internships.",
    )
    parser.add_argument(
        "--config", default="config.yaml", help="path to config.yaml"
    )
    parser.add_argument(
        "--db", default=DEFAULT_DB_PATH, help="path to the SQLite database"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="check pages and report new matches")
    p_run.add_argument(
        "--no-email",
        action="store_true",
        help="do not send email even if enabled in config",
    )
    p_run.set_defaults(func=cmd_run)

    p_list = sub.add_parser("list", help="list stored matching listings")
    p_list.add_argument("--company", help="filter by company name")
    p_list.add_argument("--limit", type=int, help="max rows to show")
    p_list.set_defaults(func=cmd_list)

    p_companies = sub.add_parser("companies", help="show configured companies")
    p_companies.set_defaults(func=cmd_companies)

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
