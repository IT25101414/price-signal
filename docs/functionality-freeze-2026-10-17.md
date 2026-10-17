# Functionality freeze — 17 October 2026

This is the stable baseline for buyer feedback, deployment and the final submission materials. Functional changes after this checkpoint should be limited to issues discovered during buyer testing; any such change must repeat the checks below.

## Frozen scope

- Daily CBSL report discovery, download, parsing, quarantine and refresh logging.
- Dambulla-to-Colombo model, calibrated 80% ranges and item-level refusal rules.
- Streamlit dashboard and Flask/SQLite website.
- Today, Explore, Weekly report, Method and Help pages.
- One-year public history slice, weekly CSV export and the saved evidence files.

## Release-safety decisions

- Estimates fail closed when the source listing cannot be checked, when a newer report is unread, when data are stale, or when model inputs are incomplete.
- A later source outage cannot erase an earlier known newer-report date.
- A failed model run still publishes the refresh safety state.
- Parser warnings quarantine a new report instead of silently accepting it.
- Website history is withheld when its latest date does not match the cards date.
- Weekly changes require all five observations in both weeks.
- Explore changes and indexing use the first and last dates shared by both series and state the paired count.
- CBSL items use different reported units; the project reports simulated savings as percentages and does not combine them into a mixed-unit rupee-per-kilogram claim.

## Verification completed

- `python3 -m pytest -q -rs`: **72 passed, 3 skipped**. The skips are the three real-PDF extractor spot checks, which need the local sample PDFs described in `test_extract_prices.py`.
- `python3 refusal_report.py`: **12 of 12** deliberate refusal cases passed.
- `python3 model.py --selftest`: passed for follower and non-follower synthetic worlds.
- `python3 robust_check.py --selftest`: passed for supported and unsupported synthetic worlds.
- `python3 decision_backtest.py --selftest`: passed for buyer-policy synthetic worlds.
- Python compilation, JavaScript syntax, shell syntax and `git diff --check`: passed.
- Browser: all five pages loaded on the current real cards and history; no console warnings or errors.
- Responsive check: Today, Explore, Weekly report, Method and Help had no page overflow at a 390 × 844 viewport.

## Not part of the functionality freeze

These submission steps remain open: real buyer feedback, public hosting, final README and licence, final technical report, two-page summary, three-minute video and private-browser submission rehearsal.
