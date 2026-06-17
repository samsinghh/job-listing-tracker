# internship-watcher

Checks internship postings from a list of companies, stores them locally in SQLite, and tells you when new matching roles appear.

## Setup

Requires Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run a check:

```bash
python -m internship_watcher run
```

View saved listings:

```bash
python -m internship_watcher list
```

See configured companies:

```bash
python -m internship_watcher companies
```

## Email Notifications

Copy the example env file:

```bash
cp .env.example .env.local
```

In `.env.local`, set `IW_SMTP_USER` (your Gmail), `IW_SMTP_PASSWORD` (a Gmail
**App Password**, not your account password), and `IW_EMAIL_TO` (where to send
alerts). `IW_EMAIL_TO` overrides `email.to` in `config.yaml`, so the committed
config keeps only a placeholder while your real address stays in `.env.local`.
Then set `email.enabled: true` in `config.yaml`.

The watcher only sends emails when it finds new listings.

## Daily Automation (macOS)

Run the watcher automatically every morning at 9 AM using `launchd`. The bundled
`deploy/com.internship-watcher.daily.plist` ships with a placeholder path; the
command below substitutes your real project path while installing it (your repo
copy stays generic):

```bash
# from the project root
PROJECT="$(pwd)"
PLIST="$HOME/Library/LaunchAgents/com.internship-watcher.daily.plist"
sed "s#/ABSOLUTE/PATH/TO/job-listing-monitor#${PROJECT}#g" \
  deploy/com.internship-watcher.daily.plist > "$PLIST"
launchctl load -w "$PLIST"
```

Verify and operate it:

```bash
launchctl list | grep internship          # confirm it's loaded (shows the label)
launchctl start com.internship-watcher.daily   # run once now, to test
cat watcher.log                            # see the latest run's output
launchctl unload -w "$PLIST"               # disable the schedule
```

Notes:

- The wrapper (`scripts/run_daily.sh`) loads `.env.local` and uses the project
  venv, so your credentials never appear in the plist.
- Prerequisites: complete **Email Notifications** above (`.env.local` filled in,
  `email.enabled: true`) so the daily run can send mail.
- If the Mac is asleep at 9 AM, `launchd` runs the job at the next wake — it
  won't silently skip the day.
- Change the time by editing `StartCalendarInterval` (`Hour`/`Minute`) in the
  installed plist, then `launchctl unload` + `load -w` to apply.

## Configuration

Everything is configured through `config.yaml`.

Example:

```yaml
companies:
  - name: Anthropic
    scraper: greenhouse
    board: anthropic
```

Supported scrapers:

- Greenhouse
- Ashby
- Lever
- Workday

Keywords and exclusions can also be configured in `config.yaml`.

## Currently Tracked

Working:

- Anthropic
- Databricks
- Stripe
- OpenAI
- NVIDIA

Not implemented yet:

- Google
- Meta
- Jane Street

## Running Tests

```bash
pytest
```

## Notes

- Local-first: SQLite database, no cloud services.
- No paid APIs.
- Credentials stay in `.env.local` and are never committed.
- Designed to be easy to extend with new companies and scrapers.
