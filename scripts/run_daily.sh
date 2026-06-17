#!/bin/bash
# Wrapper invoked by launchd (or cron). Runs the watcher with the project venv
# and loads SMTP credentials from a gitignored .env.local, so secrets live
# neither in the repo nor in the launchd plist.
set -euo pipefail

# Resolve the project root (this script lives in scripts/).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

# Load credentials if present (KEY=value or export KEY=value lines).
if [ -f .env.local ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env.local
  set +a
fi

exec .venv/bin/python -m internship_watcher run
