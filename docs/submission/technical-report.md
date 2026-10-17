# Price Signal

## Technical report — ModelX 2.0 Phase 2 implementation

**Author:** Nivetha Ramanan, Sri Lanka Institute of Information Technology  
**Domain:** Economy and livelihoods — cost of living and everyday economics  
**Repository:** <https://github.com/IT25101414/price-signal>  
**Release reviewed:** `v1.0.0-rc1`, with the 17 October 2026 interface update  
**Data shown by the committed build:** Statistics Department, Central Bank of Sri Lanka Daily Price Report, 15 October 2026  
**Public application:** `[PENDING — add the Render URL after owner-authorised deployment]`

## 1. Executive summary

Small canteens, restaurants and shops in Colombo can see today's wholesale and retail prices, but not whether an unusual move at Dambulla is likely to appear later at Pettah or Narahenpita. Price Signal converts the Central Bank of Sri Lanka's Daily Price Reports into a guarded estimate of how much of an unusual Dambulla-to-Colombo price gap may close in the next three report days.

The completed system has a polite, resumable PDF collector; a position-based table extractor; time-ordered models; calibrated uncertainty ranges; a fail-closed guard; daily refresh and publication scripts; a Streamlit dashboard; and a six-page Flask/SQLite website. The interface always states its data date and never says “buy” or “sell”. When the evidence is stale, unread, incomplete or too weak, the server removes the prices and estimate and gives a reason.

On held-out data from 2024 onward, adding Dambulla information improved forecasts beyond an own-history model in all three Colombo series. At three report days, the improvement in squared-error skill was 9.7 percentage points for wholesale Pettah, 8.3 for retail Pettah and 12.1 for retail Narahenpita. The stated 80% ranges contained 77.4% to 81.5% of unseen three-day outcomes. In a simulation, following the Dambulla model cost 1.22% to 1.57% less than always buying today. These are modest modelling results, not observed buyer savings.

The implementation is frozen and verified: 73 automated tests pass; three optional extractor tests are skipped because their real-PDF fixtures are intentionally not published; all 12 deliberate refusal cases pass; and the model, robustness and decision-policy synthetic self-tests pass. Real buyer feedback and public deployment remain pending external actions and are not claimed as complete.

## 2. Proposal versus implementation

| Proposal commitment | Result | Evidence |
|---|---|---|
| Respect robots.txt and the 10-second crawl delay | Complete | `download_cbsl_reports.py`, `data/manifest.csv` |
| Extract Daily Price Report tables and reject unknown layouts | Complete | `extract_prices.py`, `failed_files.txt` |
| Test whether Dambulla adds forecast value | Complete | `leadlag_check.py`, `robust_check.py`, saved result files |
| Compare with a placebo and own-history model | Complete | All saved lead-lag and robustness tables |
| Calibrate an 80% uncertainty range | Complete | `model.py`; 77.4%–81.5% coverage at three days |
| Test decision value | Complete as a simulation | `decision_backtest.py`; limitations stated |
| Refuse unsafe or unsupported output | Complete | `guard.py`; 12/12 refusal cases pass |
| Current user interface | Complete locally | Welcome, Today, Explore, Weekly report, Method and Help |
| Daily cloud schedule | Deliberately replaced | `run_daily.sh`; the full generated price table is not republished |
| Gradient-boosting challenger | Completed, not adopted | Ridge retained under the pre-declared rule |
| Two or three buyer sessions | Pending | Protocol is ready; no outcomes invented |
| Public deployment | Prepared, pending owner sign-in | `render.yaml`, `web/DEPLOY.md` |

## 3. User, problem and delivered insight

The named user is a small Colombo food buyer who may decide whether to buy the full amount today, split a purchase or wait. CBSL reports show current prices and a short comparison, but they do not quantify whether the Dambulla market leads a selected Colombo market, how much an unusual gap tends to close or how uncertain that relationship is.

Price Signal delivers that missing comparison. For each supported food and Colombo series it shows the latest Dambulla and Colombo prices, the deviation from the usual market gap, the expected three-report-day Colombo change, an 80% likely range and a plain-language strength label. The project does not turn the estimate into purchasing advice. It gives evidence with its limits, leaving stock, spoilage, transport, cash flow and urgency to the buyer.

## 4. Data, access and temporality

The source is the Statistics Department, Central Bank of Sri Lanka, Daily Price Report. The collector discovered 2,274 manifest records through 15 October 2026; 2,273 have an `ok` download status and one is recorded as a failed PDF download. The supported analysis begins on 28 July 2020. Older layouts, scans without a text layer, undated headers and an exact duplicate are rejected rather than guessed.

The data are both historical and current. Years of history are required to learn and test the relationship, while the latest accepted report drives the user interface. `refresh.py` checks the newest listing, downloads and parses unseen reports, appends accepted data once and records each run. The committed cards and one-year public history slice end on 15 October 2026.

The source contains important irregularities: report layouts change; some cells are blank while others explicitly say “n.a.”; markets may be closed; item names drift; prices are rounded; and Monday reports often compare with Friday. The extractor keeps these states distinct and records the comparison basis. A disagreement between one report's summary and table is retained as a documented source issue.

CBSL replied in writing on 12 October 2026 that the published data are publicly available and do not require specific approval for use, asked for attribution to the Statistics Department and stated that it does not endorse or accept responsibility for derived findings. A redacted copy is committed in `docs/cbsl_reply_2026-10-12.pdf`. The raw PDF archive and complete generated price table are not redistributed. No personal data are used.

## 5. Architecture and stack

Data moves in one direction:

`CBSL listing and PDFs → refresh/collector → position-based parser → local price table → ridge model → safety guard → cards/SQLite → website and dashboard`

The guard is the only route to user-visible estimates. It runs when cards are built and again on every web request, because a previously safe card may become stale later.

Python 3.9 is used end to end. Requests and `urllib.robotparser` provide explicit crawling behaviour; pdfplumber exposes word positions required by the parser; pandas and NumPy support data preparation and the closed-form ridge models; Flask and SQLite serve a small inspectable web application; and pytest plus GitHub Actions provide repeatable checks. The public pages use plain HTML, CSS and JavaScript with no CDN or build step.

The web product contains:

- a plain-language Welcome page with a prominent independent-project notice;
- Today, with source health, summary counts, an uncertainty chart, filters, detailed cards and guarded CSV export;
- Explore, with paired Dambulla and Colombo history and their gap;
- Weekly report, comparing two complete five-report-day windows;
- Method, presenting saved evaluation evidence; and
- Help, explaining labels, limitations and safe refusal.

## 6. Modelling method

The target is the log change in a Colombo series over one, three or five future report days. The production interface uses three. Model C uses the Colombo series' own one-day and five-day changes and its distance from its 20-day mean. Model D adds Dambulla's recent changes and the Dambulla-minus-Colombo gap relative to its trailing 60-day average. The difference in their performance measures what Dambulla adds beyond the price's own history.

Training and testing are ordered by time. Evaluation models fit data through 2023 and test on 2024 onward; labels that cross a split are dropped. Robustness intervals resample complete months, preserving local dependence. The live interval is split-conformal: residuals from a calibration period are scaled by recent item volatility, and their 80th percentile determines the likely range.

The “no clear signal” cutoff is determined on training data. A gradient-boosting challenger was evaluated under a rule fixed in advance: adopt it only when it improves three-day skill by at least 0.5 points in every Colombo series and its interval stays above zero. It failed that rule, so the simpler ridge model was retained.

## 7. Evaluation

### 7.1 Forecast value

The latest saved lead-lag run shows three-day squared-error skill gains of +9.7 points for wholesale Pettah, +8.3 for retail Pettah and +12.1 for retail Narahenpita. Gains are positive at one, three and five days. The robustness analysis' month-resampled intervals remain above zero while an item-swapped placebo is approximately zero. This supports a real but modest Dambulla lead.

### 7.2 Honest uncertainty

At three report days, the nominal 80% ranges contain 81.0% of wholesale Pettah outcomes, 81.5% of retail Pettah outcomes and 77.4% of retail Narahenpita outcomes. All are within the proposal's 75%–85% acceptance band. Average half-widths are wide—18.1% to 28.1%—so the interface foregrounds the range rather than presenting the point estimate as certainty.

### 7.3 Simulated decision value

The simulated policy chooses whether to buy today or after three report days, using thresholds fixed before the test period. Against always buying today, the Dambulla model is 1.42% cheaper for wholesale Pettah, 1.22% cheaper for retail Pettah and 1.57% cheaper for retail Narahenpita. Directional accuracy across all calls is 62% to 69%, rising to 75% to 85% for the strongest quarter. The simulation assumes the purchase can be delayed without shortage, spoilage or operational cost, so it is not evidence of actual buyer savings.

### 7.4 Safe failure and software verification

Twelve constructed cases test fresh data, staleness, a newer unread report, Colombo or Dambulla closure, missing or `n.a.` prices, too little data, no clear signal and a holiday-adjusted freshness boundary. All 12 produce the specified state. Server tests verify that withheld cards and history contain no protected figures and that the interface never says “buy” or “sell”.

On 17 October 2026, `pytest` reported 73 passed and three skipped. The skipped checks compare extracted values with private sample PDFs; their expected values remain in the test file, but the source PDFs are not in the public repository. The model, robustness and decision self-tests all pass on synthetic worlds with known answers. Python source compilation succeeds when its bytecode cache is directed to a writable project or temporary directory.

## 8. What the user sees and why it is trustworthy

Every page names the report date and data source. Direction is carried by signs, arrows and words rather than colour alone. A card combines the latest two prices with the estimated change and likely range. The strongest-signal list is a way to navigate, not a claim that the estimate is certain.

If the source listing cannot be checked, if it lists a newer unread report, if the data exceed three working days, or if an item's inputs are incomplete, the website removes numbers server-side. Weekly comparisons require five observations in both weeks. Historical comparisons require dates shared by both series. These choices reduce apparent coverage, but they prevent a polished interface from hiding weak evidence.

## 9. Limitations and unresolved work

- Real buyers have not yet used the system. The central behavioural claim—whether a buyer understands and would act on a card—remains untested. A structured, consent-based protocol is ready in `docs/buyer-feedback/`.
- The public Render service has not been created because it requires the repository owner to sign in, connect GitHub and approve an external service. The blueprint and verification steps are ready.
- The repository owner must choose the open-source licence. No assistant-selected legal terms have been presented as the author's decision.
- The full generated table is local, so daily publication is manual. This avoids republishing the complete derived dataset until that choice is made explicitly.
- The study covers 18–19 foods with a Dambulla wholesale series, a calm 2024–2026 test period and one main train/test split.
- Report-day horizons span weekends and holidays; the current holiday file covers 2026 and needs extension.
- Prices are rounded, and large estimated moves can still have a range that crosses zero.

## 10. Reproduction

From a clean clone with Python 3.9 or later:

```bash
python3 -m pip install -r requirements.txt
python3 download_cbsl_reports.py
python3 extract_prices.py data/raw prices_all.csv
python3 robust_check.py prices_all.csv
python3 leadlag_check.py prices_all.csv
python3 decision_backtest.py prices_all.csv
python3 model.py prices_all.csv --evaluate
python3 model.py prices_all.csv
python3 web/build_db.py
python3 web/server.py
python3 -m pytest -q -rs
python3 refusal_report.py
```

The full download takes roughly six hours because the required ten-second delay is respected. To review the interface without rebuilding the full private working table, run `python3 web/server.py`; it uses the committed cards and one-year history slice.

## 11. AI assistance and responsibility

Claude (Anthropic) and OpenAI Codex assisted with research, first drafts of code and documents, testing, review, safety hardening, the redacted permission evidence and interface work. The file-by-file account is in `AI_USE.md`. The project author ran and reviewed the work and remains responsible for the submitted system and claims.

## 12. Submission completion rule

Before this draft is labelled final, replace the pending public URL, enter only observed buyer-feedback results, record the video from that exact build and run the private-browser checklist. If no buyer session is completed, retain that as a limitation rather than implying evaluation that did not occur.

