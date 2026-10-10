# Price Signal

Telling short-lived food price swings from lasting ones in Sri Lankan markets.
ModelX 2.0 (IEEE CIS Student Chapter, IIT), domain: Economy & livelihoods.

**Status: in progress.** Data pipeline (download + extraction) works; models and
interface are not built yet. This README describes only what exists today.

## What it does today
1. `download_cbsl_reports.py` downloads the Central Bank of Sri Lanka (CBSL) *Daily Price
   Report* PDFs from https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report
   politely: it obeys robots.txt (including its 10-second crawl delay), resumes after
   interruption and writes `data/manifest.csv` (URL, date, SHA-256, status, download time).
2. `extract_prices.py` turns the PDFs into one tidy CSV row per (report, item, market).
   It reads values by position (the PDF text layer drops empty cells and splits numbers),
   reads market names from each section's own header, and **rejects layouts it was not
   built for instead of guessing** (reports before about June 2021 use a different format).
3. `test_extract_prices.py` checks the extractor against prices quoted in each report's own
   summary text (125 spot checks across 2021-2026).

## Run it
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# edit USER_AGENT in download_cbsl_reports.py (your contact email) first
python3 download_cbsl_reports.py --max-pages 2 --limit 10   # small test
python3 download_cbsl_reports.py                            # full archive, ~7 hours

python3 extract_prices.py data/raw prices_all.csv
```
Tests need sample PDFs (not committed): `SAMPLES_DIR=path/to/pdfs pytest`.

## Data
- Source: CBSL Statistics Department, Daily Price Report (2,270+ reports, 2017 to present;
  we use June 2021 onward because earlier layouts differ).
- Right to use: robots.txt permits automated access at a 10 s crawl delay.
  Written permission requested from CBSL on **[DATE]**; reply: **[PENDING / attach]**.
- Contains prices only, no personal data. Raw PDFs are not redistributed in this repo.

## Known data issues (found so far)
- Monday reports compare with "last Friday", not yesterday (the extractor records this).
- 2021 reports' summary text quotes wholesale prices; later years quote retail.
- Fish markets can be closed (for example 1-2 June 2026); recorded in `report_notes`.
- Source inconsistency: on 2 June 2022 the summary text says Dambulla beans 600 to 475 but
  the table says 605 to 475.
- Some rice and fish column headers are blank in the PDF; those rows carry `market_assumed=True`.

## Not done yet
Forecasting/anomaly models, evaluation against baselines, the user interface, and the
stale-data refusal logic described in the proposal.
