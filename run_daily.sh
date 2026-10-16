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

python3 refresh.py || echo "refresh did not add a report (see the message above)"
python3 model.py prices_all.csv || { echo "model failed; cards.csv not updated"; exit 1; }

git add -f cards.csv data/refresh_log.csv
if git diff --cached --quiet; then
    echo "cards.csv unchanged; nothing to publish"
else
    git commit -q -m "Daily cards for the latest report" && git push -q && echo "published cards.csv"
fi
