#!/bin/bash
# Appends the "refresh, guard, model and dashboard" sections to README.md and AI_USE.md, then commits and pushes.
#     cd ~/modelx && bash update_docs.sh
cd "$(dirname "$0")" || exit 1
if grep -q "10. Update (12 Oct 2026)" README.md 2>/dev/null; then
  echo "README.md already has this section; nothing appended"
else
cat >> README.md <<'EOF'

## 10. Update (12 Oct 2026): refresh, guard, model and dashboard

| File | What it does |
|---|---|
| `refresh.py` | Daily refresh: reads the CBSL index (obeying robots.txt and the 10 s crawl delay), downloads and parses any newer report, appends it to the table and logs the outcome. |
| `guard.py` | Decides per item whether a number may be shown. Refuses on stale data (over 3 working days), an unread newer report, a closed market, a missing price, too little data, or a gap too small to be a signal. |
| `model.py` | Expected 3-day change for each item and Colombo series, with a calibrated 80% range. The guard is applied to every card. Writes `cards.csv`. |
| `app.py` | Streamlit dashboard. Re-checks freshness every time it is opened and never shows a number the guard withheld. |
| `run_daily.sh` | Refresh, rebuild the cards, publish `cards.csv`. |
| `test_guard.py`, `test_refresh.py`, `test_model.py`, `test_app.py` | Tests, including deliberate refusal tests (stale data, unread report, closed market, too little data). |

**Calibration on data the model never saw (2024 onward):** the 80% range contained 81.0% (wholesale Pettah), 81.5% (retail Pettah) and 77.3% (retail Narahenpita) of outcomes, inside the 75 to 85% target. Run `python3 model.py prices_all.csv --evaluate`.

**Run the dashboard:**

```
python3 refresh.py
python3 model.py prices_all.csv
python3 -m streamlit run app.py
```

**Crawler note:** robots.txt is read with our own identifiable User-Agent (the default Python one gets HTTP 403 from the site), the 10-second crawl delay is obeyed, and the crawler stops on anything other than HTTP 200.
EOF
echo "README.md updated"
fi
if grep -q "Addendum 2" AI_USE.md 2>/dev/null; then
  echo "AI_USE.md already has this addendum; nothing appended"
else
cat >> AI_USE.md <<'EOF'

## Addendum 2: refresh, guard, model and dashboard

Claude (Anthropic) wrote first versions of `refresh.py`, `guard.py`, `model.py`, `app.py`, `run_daily.sh` and their tests (`test_refresh.py`, `test_guard.py`, `test_model.py`, `test_app.py`), and diagnosed and patched the robots.txt reading in `download_cbsl_reports.py`. We ran every test, checked the output on real data (including the interval coverage check), and reviewed everything. We are responsible for it.
EOF
echo "AI_USE.md updated"
fi
git add README.md AI_USE.md
git commit -q -m "README and AI_USE: document refresh, guard, model and dashboard

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01H36gcYR17eRMw3KAMNMj2e" && git push -q && echo "committed and pushed"
