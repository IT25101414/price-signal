#!/bin/bash
# Called by macOS launchd. Keep this wrapper small so the same tested run_daily.sh
# remains the single refresh path for manual and scheduled runs.
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/automation/daily-refresh.log"
cd "$ROOT" || exit 1

{
    echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] Starting scheduled Price Signal refresh"
    if [ ! -s prices_all.csv ]; then
        echo "Cannot refresh: prices_all.csv is missing. Build the private full-history file first."
        exit 2
    fi
    /bin/bash run_daily.sh
    rc=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] Finished with exit code $rc"
    exit "$rc"
} >> "$LOG" 2>&1
