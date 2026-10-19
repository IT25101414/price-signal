# Price Signal

**Telling short-lived food price swings from lasting ones, using the Central Bank of Sri Lanka's Daily Price Reports.**

ModelX 2.0 (IEEE CIS Student Chapter, IIT) · Domain: Cost of living and everyday economics · Author: Nivetha, SLIIT

**Status (18 Oct 2026):** functionality frozen at `v1.0.0-rc1`; the pipeline, model, safety guard, Streamlit dashboard and six-page Flask/SQLite website are built and tested. The committed cards use the 15 Oct report. Three consented buyer sessions are documented and their main comprehension problems have been addressed in the interface. The project is MIT-licensed and the report PDF reflects the current evidence; verified public hosting, insertion of its URL and recording the video remain open. See [`docs/submission/readiness.md`](docs/submission/readiness.md) for the live checklist.

---

## 1. The problem and the user

Small food buyers in Colombo (canteens, small restaurants, shops) cannot tell when a price jump at Dambulla, the main wholesale source, is about to reach Pettah or Narahenpita, so they buy vegetables at the wrong time. The Central Bank publishes the prices every working day, but only as a PDF that compares a price with yesterday or last Friday. It does not say whether a Colombo price is lagging behind Dambulla, or how much of the gap usually closes.

**Delivered output:** one card per item showing whether the buyer's market is lagging behind Dambulla, how much of the gap is expected to close within 3 report days, an 80% likely range and the date of the data. The evaluation also checks 1- and 5-report-day horizons. When the data cannot support a view, the card says "no clear signal" or gives the refusal reason. It never says "buy" or "sell".

## 2. Results so far

All results use a time split: models are fitted on data up to 2023 and tested on 2024 to October 2026. No future data is used for training.

**Finding 1: Dambulla leads Colombo prices (supported).** Adding the Dambulla price improves forecasts of Colombo price changes beyond a model that already uses the price's own history.

| Colombo series | Horizon (report days) | Gain (points) | 95% interval | Placebo gain | Items with gain | Verdict |
|---|---|---|---|---|---|---|
| Wholesale Pettah | 1 / 3 / 5 | +7.3 / +9.5 / +9.0 | +6.4 to +11.3 | 0.0 to +0.2 | 14-15 of 18 | supported |
| Retail Pettah | 1 / 3 / 5 | +6.5 / +8.4 / +7.9 | +5.5 to +10.2 | 0.0 to +0.1 | 14-16 of 19 | supported |
| Retail Narahenpita | 1 / 3 / 5 | +7.5 / +12.2 / +12.0 | +5.9 to +14.1 | -0.3 to -0.1 | 10-17 of 19 | supported (partly at 1 day) |

Gain is the share of squared forecast error removed, in percentage points, against a model with the price's own history only. The placebo swaps in another item's Dambulla price and should show nothing. Full per-row output, including per-year gains, is in `results_leadlag.txt`.

**Finding 2: it had modest value in a simulation.** A buyer who must buy once, today or 3 report days later, and follows the model, paid 1.2 to 1.6% less than always buying today. Perfect hindsight would save 3.6 to 5.4%. The direction was right 62 to 69% of the time on all calls and 75 to 85% on the strongest 25%. CBSL reports different foods in different units, so the project does not combine them into a misleading rupee-per-kilogram figure. See `results_decision.txt`.

**Finding 3 (negative result, kept on purpose): jump persistence cannot be predicted.** About 57% of one-day jumps of 15% or more persisted. Our models did no better than always guessing persistence (accuracy 56.6 to 56.7% against 57.2%, AUC 0.50 to 0.54), so we set that idea aside and pivoted to the lead-lag test above.

**Finding 4: three buyers saw potential value but needed clearer uncertainty language.** A restaurant buyer, vegetable-shop buyer and hotel/catering buyer completed structured sessions on 16-17 Oct. Median ratings were 4/5 for understanding, trust as one input and usefulness. Two of three needed help with the possible range, all three needed help or could not complete the historical comparison, and two questioned blank weekly values. The site now explains these points in plain language. This small study measures comprehension and stated intent, not actual savings; details are in `docs/buyer-feedback/findings-summary.md`.

**Finding 5: the lead-lag result survived a rolling-time stress check.** The same own-history and Dambulla models were refitted before three non-overlapping test windows from 5 May to 15 October 2026. Adding the matching Dambulla series improved the Colombo model in all 9 market-window combinations by +5.5 to +13.7 points; a deliberately wrong-item Dambulla placebo was zero or negative in all 9. A majority of individual items benefited in all 9 combinations. This recent-slice check strengthens temporal stability evidence but is not a 2022 crisis test; see `results_rolling_stress.txt`.

**Limits, stated plainly:** the effect is modest (errors roughly 4 to 8% smaller than "no change"); it rests on one train and test split; horizons count report days, so a Monday spans a weekend; only 18 to 19 items have Dambulla wholesale prices; the rupee backtest assumes a purchase can be deferred at no cost; the test period (2024 on) is calm and the signal may weaken in a crisis such as 2022.

## 3. Work done

| # | Work | Evidence in this repo |
|---|---|---|
| 1 | Downloader that obeys robots.txt (10-second crawl delay), downloads each PDF once and records a manifest. 2,274 records discovered through 15 Oct 2026; 2,273 downloads succeeded and one failed visibly. | `download_cbsl_reports.py`, `data/manifest.csv` |
| 2 | Position-based PDF table extractor. Reads each value by horizontal position, because the PDF text layer drops empty cells and splits numbers. Rejects any layout it was not built for instead of guessing. | `extract_prices.py` |
| 3 | Extractor verification: repository-owned helper tests run in CI, and an optional local validation checks 125 extracted prices against figures quoted in the original reports' summary text. | `test_extract_prices_unit.py`, `validate_extract_prices_real.py` |
| 4 | Full extraction run: **1,487 supported report days parsed from 28 Jul 2020 onward.** Older layouts and eight supported-layout exceptions are listed rather than guessed. | `failed_files.txt`, `coverage.py`, `coverage.csv` |
| 5 | Feasibility checks: jump persistence (negative), lead-lag (positive). | `jump_check.py`, `model_check.py`, `leadlag_check.py` |
| 6 | Robustness of the lead-lag signal: ridge model, placebo, month-resampled 95% intervals, per-year and per-item checks, self-test on synthetic data. | `robust_check.py`, `results_leadlag.txt` |
| 7 | Rupee backtest of the buying decision against four baselines, thresholds fixed on pre-2024 data. | `decision_backtest.py`, `results_decision.txt` |
| 8 | Written response received from CBSL on **12 Oct 2026**: the published data are publicly available, do not require specific approval for use, and should be attributed to the Statistics Department. CBSL does not endorse the project. | [`docs/cbsl_reply_2026-10-12.pdf`](docs/cbsl_reply_2026-10-12.pdf) |
| 9 | Phase 1 project proposal completed against every required competition section. | `docs/submission/phase1-project-proposal.pdf` |
| 10 | AI-use disclosure for every script and document. | `AI_USE.md` |
| 11 | Functionality frozen and independently re-checked: the current 86 reproducible tests pass with no environment-dependent skips, 12 of 12 deliberate refusal cases pass, and all model self-tests pass. | `docs/functionality-freeze-2026-10-17.md` |
| 12 | Three anonymous, consented buyer sessions completed; task results and individual ratings recorded; buyer-driven wording changes implemented. | `docs/buyer-feedback/findings-summary.md` |
| 13 | Final technical report updated from the 17 Oct version; two-page summary and three-minute video script prepared from the saved evidence. | `docs/submission/` |
| 14 | Rolling-origin stress test over three held-out 2026 windows, with wrong-item placebo. | `rolling_stress_check.py`, `results_rolling_stress.txt` |
| 15 | Reproducible accessibility regression check plus rendered-browser structure audit. | `web/accessibility_check.py`, `results_accessibility.txt` |
| 16 | Public-service smoke monitor for health, safety status and all six pages; scheduled workflow activates when the public URL is configured. | `web/smoke_test.py`, `.github/workflows/public-site-smoke.yml` |

### Coverage

| | Count |
|---|---|
| Manifest records discovered | 2,274 |
| Successful PDF downloads | 2,273 |
| Parsed (supported layout) | 1,487 report days |
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

## 4. Submission readiness and timeline

| Dates | Work | Done when |
|---|---|---|
| 10 to 19 Oct | Research, data pipeline, parser, lead-lag evidence, proposal | Proposal submitted; repository public with tests **(largely done)** |
| 20 to 22 Oct | Re-run the checks on the final data; close remaining parser gaps; handle CBSL's reply | Coverage numbers final; results re-confirmed |
| 23 to 26 Oct | Calibrated prediction intervals; extend the decision backtest | An 80% interval contains 75 to 85% of outcomes; backtest table written |
| 27 to 29 Oct | Guard and refusal rules; daily refresh; interface | Stale, missing and closed-market tests pass; dashboard runs on the latest real report |
| 30 to 31 Oct | Finalise the technical report and two-page summary after buyer feedback and public deployment; record the three-minute video | Final files reviewed by a second person |
| 1 Nov | **Implementation submission** | Repository opens from a private browser window and this README runs |
| 9 to 14 Nov | If we reach the final: rehearse the live demo | Demo runs on the day's real report |

**Still to do (18 Oct 2026):** complete and verify the public Render service; add its exact URL to the README and report; re-export the report PDF with that URL; record the final three-minute video on that public build; then complete a private-browser submission rehearsal. The buyer findings and interface changes are complete. A no-cost macOS daily refresh schedule is now included, but it can only be activated on the author's Mac after the private `prices_all.csv` full-history file is present.

**What we cut first if time runs short:** (1) additional challenger models beyond those already evaluated, (2) additional forecast horizons beyond the tested 1-, 3- and 5-report-day checks, and (3) decorative interface features. The three buyer sessions, local-language core interface, daily refresh schedule and four reporting periods are complete. We never cut the freshness check, refusal rules or honest evaluation.

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

# 3a. Reproducible automated tests (no external fixtures required)
python3 -m pytest -q

# 3b. Optional validation against locally held original reports
SAMPLES_DIR=samples python3 validate_extract_prices_real.py

# 4. Analysis
python3 coverage.py prices_all.csv
python3 jump_check.py prices_all.csv
python3 model_check.py prices_all.csv
python3 leadlag_check.py prices_all.csv
python3 robust_check.py prices_all.csv
python3 decision_backtest.py prices_all.csv
python3 rolling_stress_check.py data/recent_prices.csv

# 5. Release checks
python3 web/accessibility_check.py
python3 web/smoke_test.py http://127.0.0.1:5000
```

`prices_all.csv` and the raw PDFs are generated locally and are not redistributed in this repository.

### Automatic daily refresh on macOS

The included no-cost scheduler checks for a new CBSL report every day at 18:30 local time. It runs the same guarded pipeline as `run_daily.sh`, rebuilds the local website database, and pushes a new safety state only through the configured Git remote. CBSL normally publishes on working days, so a weekend check usually finds no new report; weekend dates do not make Friday's report stale because freshness is counted in working days.

The scheduler deliberately requires the private full-history `prices_all.csv`; the committed one-year display slice is not sufficient for valid model retraining.

```bash
# Run once after prices_all.csv has been generated in the repository root.
bash automation/install_macos_refresh.sh

# Optional: start one refresh immediately and inspect its log.
launchctl kickstart -k gui/$(id -u)/com.price-signal.refresh
tail -n 50 automation/daily-refresh.log
```

## 7. Repository map

| File | What it is |
|---|---|
| `download_cbsl_reports.py` | Polite downloader and manifest writer |
| `extract_prices.py` | PDF table extractor |
| `test_extract_prices_unit.py` | Reproducible unit tests for extractor helpers; runs in CI without external fixtures |
| `validate_extract_prices_real.py` | Optional local validation against each original report's own summary text |
| `coverage.py`, `coverage.csv` | Which item / market series are complete enough to model |
| `jump_check.py`, `model_check.py` | Jump-persistence feasibility checks (negative result) |
| `leadlag_check.py` | First lead-lag check |
| `robust_check.py`, `results_leadlag.txt` | Robust lead-lag test with placebo and intervals |
| `decision_backtest.py`, `results_decision.txt` | Rupee backtest of the buying decision |
| `rolling_stress_check.py`, `results_rolling_stress.txt` | Three chronological recent-data tests with a wrong-item placebo |
| `failed_files.txt` | Reports not parsed, with the reason |
| `data/manifest.csv` | URL, date, file hash and download time of every report |
| `AI_USE.md` | Which AI tool was used, for what |
| `docs/submission/phase1-project-proposal.pdf` | Reviewed Phase 1 proposal answering every required competition section |
| `docs/submission/technical-report-final.pdf` | Final technical report for the verified local release |
| `docs/submission/two-page-summary.pdf` | Final two-page implementation summary for the verified local release |

## 8. Data source, licence and ethics

- **Source:** Central Bank of Sri Lanka, Statistics Department, Daily Price Report: https://www.cbsl.gov.lk/en/statistics/economic-indicators/price-report
- **Access:** robots.txt permits automated access at a 10-second crawl delay and blocks only search and system paths, which we avoid.
- **Reuse response:** the Statistics Department replied on 12 Oct 2026 that the published data are publicly available and do not require specific approval or permission for use. It requested attribution to the "Statistics Department, Central Bank of Sri Lanka" and stated that CBSL bears no responsibility for, and does not endorse, derived content, findings or interpretations. A redacted public copy is in [`docs/cbsl_reply_2026-10-12.pdf`](docs/cbsl_reply_2026-10-12.pdf).
- **We do:** credit CBSL, use the data only for this non-commercial project, and keep the raw PDFs out of the repository.
- **Personal data:** none. The data are prices by item and market only.
- **Code licence:** the original software in this repository is released under the [`MIT License`](LICENSE). CBSL data, source reports, the Sri Lankan national emblem and other third-party material remain the property of their respective owners and are not relicensed by the MIT file.

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

## 11. Update (17 Oct 2026): website, holidays, CI, refusal results

- **Website** in `web/` (Flask + SQLite, no build step). Run: `python3 model.py prices_all.csv`, `python3 web/build_db.py`, `python3 web/server.py`. See `web/README.md`. The server applies the same guard on every request and withholds numbers when a report is stale, unread or not ok.
- **Public holidays:** `data/holidays.csv` (2026 public holidays, taken from a published calendar). Add `date,name` rows (YYYY-MM-DD) and the guard stops counting those days as working days. Override the file with `PRICE_SIGNAL_HOLIDAYS`.
- **Refusal results:** `python3 refusal_report.py` runs 12 synthetic cases, each with one deliberate fault, and writes `results_refusal.txt`. These test the guard's logic, not any real report.
- **CI:** `.github/workflows/tests.yml` runs the reproducible tests, refusal report, rolling stress analysis and accessibility regression on every push (Python 3.9). The verified local result on 18 Oct is **87 passed, 0 skipped**. The separate `validate_extract_prices_real.py` check uses git-ignored original PDFs and is invoked explicitly, so a fresh clone no longer reports environment-dependent skips.
- **Permission:** the Central Bank's Statistics Department replied on 12 Oct 2026 about use of the Daily Price Reports; page 1 of the reply is in `docs/cbsl_reply_2026-10-12.pdf` (contact details removed). This project is not endorsed by the Central Bank; the data is theirs, the analysis is ours.


**Pinned versions:** `requirements.lock` lists the exact versions used for the results in this repository (Python 3.9). Install them with `python3 -m pip install -r requirements.lock`; `requirements.txt` gives the minimum versions.

**Hosting (added 16 Oct 2026):** `render.yaml` and `web/DEPLOY.md` describe a free Render deployment of the website. The site is built from the committed `cards.csv` and `data/refresh_log.csv` only; `run_daily.sh` refreshes, rebuilds the cards and pushes both files, and the host rebuilds on each push. The web server answers with `Cache-Control: no-store` and uses Sri Lanka time for the freshness check. The 80% range can be checked at other horizons with `python3 model.py prices_all.csv --evaluate --h 1` (and `--h 5`).

**Website pages (added 17 Oct 2026):** Welcome gives a plain-language introduction and a prominent independent-project notice. Visitors can choose English, Sinhala or Tamil on that page; the choice persists across the site, and the core welcome, navigation, status, safety and Today-summary wording follows it. Official item, market, date and source values remain unchanged. Today shows source health, a signal summary, an expected-change and uncertainty chart, the clearest-estimate list, filters, safe CSV export and detailed cards. Explore shows past prices of any item as a chart, with the difference between Dambulla and Colombo, 1 week to 1 year, rupees or indexed to 100. Reports offers strict Daily, Weekly, Monthly and Annual comparisons, with guarded CSV download and print-to-PDF output. How it works presents the evidence charts read from `results_*.txt`; Help explains the interface. Every past-price view obeys the same guard as the cards: nothing is shown when the report is stale or a newer one is unread, and an item with missing data shows no prices. `data/recent_prices.csv` (written by `export_recent.py`, run by `run_daily.sh`) is a small slice of the Central Bank's published prices, so a fresh clone still has charts; the Central Bank's reply of 12 Oct 2026 says the data are public and asks for attribution to the Statistics Department.

**Advanced release checks (added 18 Oct 2026):** `rolling_stress_check.py` refits the three-day model before three non-overlapping recent test windows; all nine market-window gains were positive and all nine wrong-item placebo gains were non-positive. `web/accessibility_check.py` checks all six source pages and the principal light/dark contrast pairs in CI; the rendered pages were also inspected for accessible names and structure. `web/smoke_test.py` verifies `/healthz`, `/api/status` and every public page. The scheduled smoke workflow starts automatically after the repository owner sets the `PUBLIC_SITE_URL` repository variable. The verified local suite now reports **93 passed, 0 skipped**.

