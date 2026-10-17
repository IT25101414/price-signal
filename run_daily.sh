#!/bin/bash
# Daily update: fetch the newest Central Bank report (if any), rebuild today's cards, publish them.
#
#     bash run_daily.sh
#
# 1. refresh.py   reads the site's index (obeying robots.txt and the 10 s crawl delay), downloads and
#                 parses any report newer than the table, appends it, and logs the outcome.
#                 If the site is down or a report cannot be parsed, it says so and adds nothing.
# 2. model.py     recomputes every item's gap, expected change and 80% range, and applies the guard.
#                 It runs even when step 1 added nothing, so a stale table produces refusals, not old numbers.
# 3. git          publishes cards.csv and the refresh log; the hosted website rebuilds from them.
cd "$(dirname "$0")" || exit 1

refresh_rc=0
python3 refresh.py || { refresh_rc=$?; echo "refresh could not complete (see the message above)"; }

model_rc=0
python3 model.py prices_all.csv || { model_rc=$?; echo "model failed; cards.csv not updated"; }

if [ "$model_rc" -eq 0 ]; then
    python3 export_recent.py prices_all.csv || echo "recent price slice not updated"
    git add -f cards.csv data/refresh_log.csv data/recent_prices.csv 2>/dev/null || git add -f cards.csv data/refresh_log.csv
else
    # Publishing the refresh log is safety-critical: it can tell the hosted guard to hide old cards.
    git add -f data/refresh_log.csv
fi
publish_rc=0
if git diff --cached --quiet; then
    echo "nothing changed; nothing to publish"
else
    git commit -q -m "Daily cards for the latest report" && git push -q && echo "published daily state" || publish_rc=$?
fi

if [ "$publish_rc" -ne 0 ]; then
    echo "could not publish the daily safety state"
    exit "$publish_rc"
fi
if [ "$model_rc" -ne 0 ]; then
    exit "$model_rc"
fi
if [ "$refresh_rc" -ne 0 ]; then
    echo "published a fail-closed refresh state"
fi
