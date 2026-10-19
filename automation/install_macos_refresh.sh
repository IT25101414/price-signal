#!/bin/bash
# Install a no-cost per-user macOS schedule: every day at 18:30 local time.
set -eu

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/automation/com.price-signal.refresh.plist.template"
AGENTS="$HOME/Library/LaunchAgents"
PLIST="$AGENTS/com.price-signal.refresh.plist"

if [ ! -s "$ROOT/prices_all.csv" ]; then
    echo "Not installed: $ROOT/prices_all.csv is missing."
    echo "Build the private full-history file first; the public recent slice is not valid for retraining."
    exit 2
fi

mkdir -p "$AGENTS"
escaped_root=$(printf '%s' "$ROOT" | sed 's/[&|]/\\&/g')
sed "s|__REPO__|$escaped_root|g" "$TEMPLATE" > "$PLIST"
chmod 600 "$PLIST"

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "Installed: Price Signal will check for a new report every day at 18:30 local time."
echo "Log: $ROOT/automation/daily-refresh.log"
echo "Run once now: launchctl kickstart -k gui/$(id -u)/com.price-signal.refresh"
