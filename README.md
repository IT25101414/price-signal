# Price Signal

**Telling short-lived food price swings from lasting ones, using the Central Bank of Sri Lanka's Daily Price Reports.**

ModelX 2.0 (IEEE CIS Student Chapter, IIT) · Domain: Cost of living and everyday economics · Author: Nivetha, SLIIT

**Status (16 Oct 2026):** pipeline, refresh, guard, model, Streamlit dashboard and Flask/SQLite website built and tested; proposal ready for 19 Oct. See section 11 for the latest changes.

---

## 1. The problem and the user

Small food buyers in Colombo (canteens, small restaurants, shops) cannot tell when a price jump at Dambulla, the main wholesale source, is about to reach Pettah or Narahenpita, so they buy vegetables at the wrong time. The Central Bank publishes the prices every working day, but only as a PDF that compares a price with yesterday or last Friday. It does not say whether a Colombo price is lagging behind Dambulla, or how much of the gap usually closes.

**Planned output:** one card per item showing whether the buyer's market is lagging behind Dambulla, how much of the gap has typically closed within 1, 3 and 5 report days, how uncertain that is, and the date of the data. When the data cannot support a view the card says "no clear signal" or "insufficient data". It never says "buy" or "sell".

## 2. Results so far

All results use a time split: models are fitted on data up to 2023 and tested on 2024 to October 2026. No future data is used for training.

**Finding 1: Dambulla leads Colombo prices (supported).** Adding the Dambulla price improves forecasts of Colombo price changes beyond a model that already uses the price's own history.

| Colombo series | Horizon (report days) | Gain (points) | 95% interval | Placebo gain | Items with gain | Verdict |
|---|---|---|---|---|---|---|
| Wholesale Pettah | 1 / 3 / 5 | +7.3 / +9.5 / +9.0 | +6.4 to +11.3 | 0.0 to +0.2 | 14-15 of 18 | supported |
| Retail Pettah | 1 / 3 / 5 | +6.5 / +8.4 / +7.9 | +5.5 to +10.2 | 0.0 to +0.1 | 14-16 of 19 | supported |
| Retail Narahenpita | 1 / 3 / 5 | +7.5 / +12.2 / +12.0 | +5.9 to +14.1 | -0.3 to -0.1 | 10-17 of 19 | supported (partly at 1 day) |

Gain is the share of squared forecast error removed, in percentage points, against a model with the price's own history only. The placebo swaps in another item's Dambulla price and should show nothing. Full per-row output, including per-year gains, is in `results_leadlag.txt`.

**Finding 2: it is worth something in rupees (simulation).** A buyer who must buy once, today or 3 report days later, and follows the model, paid 1.2 to 1.6% less than always buying today (about Rs 60 to 96 per 10 kg). Perfect hindsight would save 3.6 to 5.4%. The direction was right 62 to 69% of the time on all calls and 75 to 85% on the strongest 25%. See `results_decision.txt`.

**Finding 3 (negative result, kept on purpose): jump persistence cannot be predicted.** About 57% of one-day jumps of 15% or more persisted. Our models did no better than always guessing persistence (accuracy 56.6 to 56.7% against 57.2%, AUC 0.50 to 0.54), so we set that idea aside and pivoted to the lead-lag test above.

**Limits, stated plainly:** the effect is modest (errors roughly 4 to 8% smaller than "no change"); it rests on one train and test split; horizons count report days, so a Monday spans a weekend; only 18 to 19 items have Dambulla wholesale prices; the rupee backtest assumes a purchase can be deferred at no cost; the test period (2024 on) is calm and the signal may weaken in a crisis such as 2022.

## 3. Work done

| # | Work | Evidence in this repo |
|---|---|---|
| 1 | Downloader that obeys robots.txt (10-second crawl delay), downloads each PDF once and records a manifest. 2,269 report PDFs retrieved (Apr 2017 to Oct 2026). | `download_cbsl_reports.py`, `data/manifest.csv` |
| 2 | Position-based PDF table extractor. Reads each value by horizontal position, because the PDF text layer drops empty cells and splits numbers. Rejects any layout it was not built for instead of guessing. | `extract_prices.py` |
| 3 | Tests: 125 extracted prices checked against figures quoted in each report's own summary text. | `test_extract_prices.py` |
| 4 | Full extraction run: **1,485 report days parsed (28 Jul 2020 to 9 Oct 2026), 268,213 price rows.** | `failed_files.txt`, `coverage.py`, `coverage.csv` |
| 5 | Feasibility checks: jump persistence (negative), lead-lag (positive). | `jump_check.py`, `model_check.py`, `leadlag_check.py` |
| 6 | Robustness of the lead-lag signal: ridge model, placebo, month-resampled 95% intervals, per-year and per-item checks, self-test on synthetic data. | `robust_check.py`, `results_leadlag.txt` |
| 7 | Rupee backtest of the buying decision against four baselines, thresholds fixed on pre-2024 data. | `decision_backtest.py`, `results_decision.txt` |
| 8 | Written permission requested from CBSL on **11 Oct 2026**; reply: **none yet**. | this README |
| 9 | Phase 1 project proposal written. | submitted for 19 Oct |
| 10 | AI-use disclosure for every script and document. | `AI_USE.md` |

### Coverage

| | Count |
|---|---|
| Report files downloaded | 2,269 |
| Parsed (current layout) | 1,485 of 1,493 in-scope reports |
| Older layouts (2017 to mid-2020), rejected on purpose | 776 |
| Scanned PDFs with no text layer (2022-03-16, 2025-09-24, 2025-09-25, 2026-04-15) | 4 |
| Header names a weekday but no date (2026-04-02, 2026-05-29, 2026-07-30) | 3 |
| Exact duplicate file (2022-06-22 is a copy of 21 June) | 1 |

Unparsed reports are listed in `failed_files.txt`. Nothing is guessed or filled in silently.

### Known data issues

- Comparison basis varies ("Yesterday", "Last Friday", "Friday dd.mm.yyyy"); it is stored with every row.
- Item names drift across years (case, "(lmp)" and "(Imp)", "Dhal" and "Red Dhal"); they are normalised in the analysis scripts.
- "n.a." (no price reported), a blank cell (not applicable) and a closed market (footnote) are different things and are kept apart.
- Prices are rounded to the nearest Rs 5 or 10, so cheap items move in steps.
- One report (2 June 2022) quotes a summary figure that disagrees with its own table; we follow the table.
- Some column headers are blank in the PDF; those rows are flagged as assumed.
- Some pages are scaled differently, carry footnote markers inside prices, or have a file date that differs from the report date. The extractor handles these.
- About 0.5% of compared prior-versus-today pairs differ across consecutive reports; they are flagged.

## 4. Work to do, and timeline

| Dates | Work | Done when |
|---|---|---|
| 10 to 19 Oct | Research, data pipeline, parser, lead-lag evidence, proposal | Proposal submitted; repository public with tests **(largely done)** |
| 20 to 22 Oct | Re-run the checks on the final data; close remaining parser gaps; handle CBSL's reply | Coverage numbers final; results re-confirmed |
| 23 to 26 Oct | Calibrated prediction intervals; extend the decision backtest | An 80% interval contains 75 to 85% of outcomes; backtest table written |
| 27 to 29 Oct | Guard and refusal rules; daily refresh; interface | Stale, missing and closed-market tests pass; dashboard runs on the latest real report |
| 30 to 31 Oct | Technical report, two-page summary, three-minute video; buyer feedback (2 to 3 buyers) | Drafts reviewed by a second person |
| 1 Nov | **Implementation submission** | Repository opens from a private browser window and this README runs |
| 9 to 14 Nov | If we reach the final: rehearse the live demo | Demo runs on the day's real report |

**Still to do (16 Oct 2026):** buyer interviews, hosting the website, a scheduled cloud refresh, and the two-page summary and video. Built and tested: refresh, guard (with holiday support), model with calibrated ranges, Streamlit dashboard, Flask and SQLite website, refusal report and CI.

**What we cut first if time runs short:** (1) gradient-boosting challenger models, (2) Sinhala and Tamil versions of the interface, (3) automated daily refresh, replaced by a script the user runs, (4) the 1-day and 5-day horizons, keeping 3 days, (5) buyer interviews reduced from 3 to 1 or 2. We never cut the freshness check, the refusal rules or the honest evaluation.

## 5. Final outcome we are aiming for

- A public repository whose README runs from a clean machine.
- A dashboard of cards built from the latest real report, each with its data date.
- Refusal rules that are tested: stale data, a rejected report, a closed market, too little data, a missing Dambulla price.
- A technical report that evaluates the system honestly against the proposal, and a three-minute video of it working on real data.

If the lead-lag signal does not hold on the final data, we say so, stop claiming a lead, and ship the honest version: the data date, the Dambulla-to-Colombo gap, and a clear "no reliable signal" label with no forecast.

## 6. How to run it

```bash
pip install -r requirements.txt

# 1. Download the reports (obeys robots.txt; 10 s between requests; resumes automatically)
python3 download_cbsl_reports.py --limit 10     # try 10 first
python3 download_cbsl_reports.py                # full run

# 2. Extract prices (writes failed_files.txt and warnings.txt in the current folder)
python3 extract_prices.py data/raw prices_all.csv

# 3. Tests (needs the sample PDFs listed in test_extract_prices.py)
SAMPLES_DIR=samples python3 test_extract_prices.py

# 4. Analysis
python3 coverage.py prices_all.csv
python3 jump_check.py prices_all.csv
python3 model_check.py prices_all.csv
python3 leadlag_check.py prices_all.csv
python3 robust_check.py prices_all.csv
python3 decision_backtest.py prices_all.csv
```

`prices_all.csv` and the raw PDFs are generated locally and are not redistributed in this repository.

## 7. Repository map

| File | What it is |
|---|---|
| `download_cbsl_reports.py` | Polite downloader and manifest writer |
| `extract_prices.py` | PDF table extractor |
| `test_extract_prices.py` | Extractor tests against each report's own summary text |
| `coverage.py`, `coverage.csv` | Which item / market series are complete enough to model |
| `jump_check.py`, `model_check.py` | Jump-persistence feasibility checks (negative result) |
| `leadlag_check.py` | First lead-lag check |
| `robust_check.py`, `results_leadlag.txt` | Robust lead-lag test with placebo and intervals |
| `decision_backtest.py`, `results_decision.txt` | Rupee backtest of the buying decision |
| `failed_files.txt` | Reports not parsed, with the reason |
| `data/manifest.csv` | URL, date, file hash and download time of every report |
| `AI_USE.md` | Which AI tool was used, for what |

## 8. Data source, licence and ethics

- **Source:** Central Bank of Sri Lanka, Statistics Department, Daily Price Report: https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report
- **Access:** robots.txt permits automated access at a 10-second crawl delay and blocks only search and system paths, which we avoid.
- **Reuse terms:** we have not found a statement of reuse terms on the CBSL site. Written permission was requested on 11 Oct 2026; reply: none yet. This section will be updated when CBSL replies.
- **We do:** credit CBSL, use the data only for this non-commercial project, and keep the raw PDFs out of the repository.
- **Personal data:** none. The data are prices by item and market only.

## 9. AI assistance

Claude (Anthropic) helped research data sources and literature, write first versions of the scripts and draft the proposal. We ran, tested and reviewed everything and are responsible for it. Details: [`AI_USE.md`](AI_USE.md).

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

## 11. Update (16 Oct 2026): website, holidays, CI, refusal results

- **Website** in `web/` (Flask + SQLite, no build step). Run: `python3 model.py prices_all.csv`, `python3 web/build_db.py`, `python3 web/server.py`. See `web/README.md`. The server applies the same guard on every request and withholds numbers when a report is stale, unread or not ok.
- **Public holidays:** `data/holidays.csv` (header only, no dates invented). Add `date,name` rows (YYYY-MM-DD) and the guard stops counting those days as working days. Override the file with `PRICE_SIGNAL_HOLIDAYS`.
- **Refusal results:** `python3 refusal_report.py` runs 12 synthetic cases, each with one deliberate fault, and writes `results_refusal.txt`. These test the guard's logic, not any real report.
- **CI:** `.github/workflows/tests.yml` runs the tests and the refusal report on every push (Python 3.9). Tests that need the git-ignored sample PDFs are skipped when those are absent.
- **Permission:** the Central Bank's Statistics Department replied on 12 Oct 2026 about use of the Daily Price Reports; page 1 of the reply is in `docs/cbsl_reply_2026-10-12.pdf` (contact details removed). This project is not endorsed by the Central Bank; the data is theirs, the analysis is ours.

