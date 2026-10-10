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
   built for instead of guessing** (reports before late July 2020 use older formats).
   Every unparsed file is listed with its reason in `failed_files.txt`.
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
The summary printed at the end shows parsed/failed files per year. The full lists of
failures and warnings are written to `failed_files.txt` and `warnings.txt`.

Tests need sample PDFs (not committed): `SAMPLES_DIR=path/to/pdfs python3 test_extract_prices.py`
(or `pytest`). The samples are the reports for 1-2 June 2021-2026 (plus 3-4 June 2021 and
2024), 2-9 October 2026, and 1-2 June 2020 (which must be rejected as an older layout).

## Coverage (full run, 10 October 2026)
| | Count |
|---|---|
| PDF files downloaded (2017-04 to 2026-10) | 2,269 |
| Reports parsed | 1,485 report days, **2020-07-28 to 2026-10-09** |
| Rows in `prices_all.csv` | 268,213 (no duplicate report/item/market rows) |
| Not parsed: older layouts (2017 to mid-2020) | 776, rejected on purpose |
| Not parsed: scanned PDFs with no text | 4 (2022-03-16, 2025-09-24, 2025-09-25, 2026-04-15) |
| Not parsed: header names a weekday but no date | 3 (2026-04-02, 2026-05-29, 2026-07-30) |
| Skipped: exact duplicate file | 1 (`2022-06-22__...20220621_0.pdf` is a copy of 21 June 2022) |

Cross-day check: each report states the previous price, so "today" in one report should
equal "prior" in the next. About 0.5% of the compared pairs (1,125 of 208,019 before the
final clean-up) differ; the ones inspected are discrepancies inside the CBSL reports.

## Data
- Source: CBSL Statistics Department, Daily Price Report (2,269 files, 2017 to present;
  the current extractor covers 28 July 2020 onward, 2017 to mid-2020 uses older layouts).
- Right to use: robots.txt permits automated access at a 10 s crawl delay.
  Written permission requested from CBSL on **[DATE]**; reply: **[PENDING / attach]**.
- Contains prices only, no personal data. Raw PDFs are not redistributed in this repo.

## Known data issues (found so far)
- Monday reports compare with "last Friday", not yesterday; a few others compare with
  "last Tuesday" or "last Wednesday" (public holidays). The extractor records the comparison
  day in `prior_label` and `prior_date`.
- 2021 reports' summary text quotes wholesale prices; later years quote retail.
- Fish markets can be closed (for example 1-2 June 2026); recorded in `report_notes`.
- Source inconsistency: on 2 June 2022 the summary text says Dambulla beans 600 to 475 but
  the table says 605 to 475.
- Some rice and fish column headers are blank in the PDF; those rows carry `market_assumed=True`.
- No report in the data for 22 June 2022 (the file listed under that date is a copy of 21 June).
- Some prices carry a footnote marker such as `150.00(a)`; the marker is dropped and the number kept.
- Some 2020-2021 reports are laid out about 1.5 times larger than the rest; the extractor
  scales its column positions to match.
- Dates in some downloaded file names are wrong (for example a 2020 report filed under 2023);
  the extractor uses the date printed inside each report and warns when it differs from the name.

## Not done yet
Forecasting/anomaly models, evaluation against baselines, the user interface, and the
stale-data refusal logic described in the proposal. Reports before late July 2020 are not
parsed (they need a separate extractor for the older layout).
