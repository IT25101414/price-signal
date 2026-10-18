# AI assistance disclosure (required by ModelX 2.0 rules)

| Tool | Used for |
|---|---|
| Claude (Anthropic) | Researching data sources, drafting the project proposal, writing first versions of `download_cbsl_reports.py`, `extract_prices.py` and the real-report extractor validation now named `validate_extract_prices_real.py`, and explaining PDF layouts. |

We ran, tested and reviewed everything before committing and take responsibility for it.
Update this table whenever the use of AI tools changes.

## Addendum: all scripts and documents where Claude (Anthropic) helped

Claude wrote first versions of these analysis scripts. We ran each one, checked its output, and changed it where needed:

- `coverage.py` (coverage report for the price table)
- `jump_check.py` (do one-day price jumps persist?)
- `model_check.py` (can a model predict which jumps persist?)
- `leadlag_check.py` (does Dambulla lead Colombo prices?)
- `robust_check.py` (ridge model, placebo test, month-resampled intervals)
- `decision_backtest.py` (rupee backtest of the buying decision)

Claude also researched data sources and literature, drafted the project proposal including the literature review, and explained PDF layouts. We ran, tested and reviewed everything, and we are responsible for it.

## Addendum 2: refresh, guard, model and dashboard

Claude (Anthropic) wrote first versions of `refresh.py`, `guard.py`, `model.py`, `app.py`, `run_daily.sh` and their tests (`test_refresh.py`, `test_guard.py`, `test_model.py`, `test_app.py`), and diagnosed and patched the robots.txt reading in `download_cbsl_reports.py`. We ran every test, checked the output on real data (including the interval coverage check), and reviewed everything. We are responsible for it.

## Addendum 3: website, holidays, refusal report and CI

Claude (Anthropic) wrote first versions of the Flask server, the SQLite loader and schema, the web page (`web/static/`), `web/test_web.py`, holiday support in `guard.py` with its tests, `refusal_report.py`, the GitHub Actions workflow, and the README and proposal edits for the Central Bank's reply. We ran the tests, looked at the pages in a browser, and reviewed everything. We are responsible for it.


## Addendum 4: hosting files and server hardening

Claude (Anthropic) wrote the Render blueprint (`render.yaml`), the deployment guide (`web/DEPLOY.md`), the Sri Lanka time handling, cache headers and logging in `web/server.py`, their tests, and the change to `run_daily.sh` that also publishes the refresh log. We ran the tests and the production server command and reviewed everything. We are responsible for it.

## Addendum 6: website pages and history slice

Claude (Anthropic) wrote the first versions of the Explore, Weekly report, How it works and Help pages (`web/static/`), the routes and result-file reader behind them (`web/server.py`, `web/evidence.py`), `export_recent.py`, the history fallback in `web/build_db.py`, and their tests. We ran the tests, looked at every page on desktop and phone in light and dark themes, and reviewed everything. We are responsible for it.

## Addendum 7: CBSL permission evidence

OpenAI Codex inspected the CBSL email reply for personal contact information, produced the one-page redacted public copy in `docs/cbsl_reply_2026-10-12.pdf`, and corrected the README's earlier "no reply yet" statements. The original email PDF remains private. We reviewed the redacted copy against the original and are responsible for publishing it.

## Addendum 8: functionality-freeze audit

OpenAI Codex audited the pipeline, model, publication script, Flask APIs and browser interface before the functionality freeze. It implemented fail-closed handling when the CBSL listing cannot be checked, retained the last known listed report date across outages, prevented incomplete model inputs from producing an `ok` card, made refresh tests independent of private PDF fixtures, required weekly averages to contain all five observations, corrected paired-date calculations on Explore, withheld mismatched history, pinned the tested web deployment dependencies, and removed a mixed-unit rupee-per-10-kg claim. It also added the corresponding regression tests and accessibility wording changes. We ran the full automated suite, model self-tests, refusal report, desktop browser checks and a 390 px mobile-layout check; the verification record is in `docs/functionality-freeze-2026-10-17.md`. The project author remains responsible for reviewing and submitting the work.

## Addendum 9: command centre and welcome page

OpenAI Codex expanded the Today interface with summary cards, an expected-change and uncertainty chart, strongest-signal list, filters, CSV export and data-safety checks. It then created the plain-language welcome page, simplified technical interface labels and added the supplied Sri Lanka emblem with a prominent independent-project notice. OpenAI's image tool removed the supplied image's checkerboard background and separate label to create `web/static/sri-lanka-national-emblem-clean.png`; the emblem design itself was retained. We tested the routes, scripts, responsive layout, navigation and browser console, and the project author remains responsible for reviewing and publishing the result.

## Addendum 10: submission pack

OpenAI Codex checked the final repository state against the ModelX 2.0 implementation rules, reconciled saved metrics with the code and test outputs, and drafted `docs/submission/technical-report.md`, `two-page-summary.md`, `video-script.md`, `readiness.md` and `private-browser-check.md`. It then updated the author's 17 October 16-page report with the six-page interface, command-centre features, 73-test result, current AI disclosure and an implementation-update page, producing `docs/submission/technical-report-final.pdf`. Every edited page was rendered and visually checked. At that stage, pending buyer results and the public URL were labelled rather than invented. The project author must review, complete and approve these materials before submission.

## Addendum 11: reproducibility and buyer-feedback revision

OpenAI Codex separated the optional original-PDF validation from default pytest discovery and added repository-owned extractor helper tests, so a fresh clone no longer reports environment-dependent skips. The project author then supplied three anonymised participant records, session dates and confirmation of permission to publish the anonymous responses. OpenAI Codex aggregated only those supplied observations, updated the submission documents and added plain-language explanations for the possible range, shared report days, the start-at-100 comparison, blank weekly values and source-data date. It also added a regression check for those explanations. OpenAI Codex did not generate participant outcomes. The author reviewed the records and remains responsible for their accuracy and publication.

## Addendum 12: advanced release evidence

OpenAI Codex added the rolling-origin recent-data stress test, public-service smoke checker and weekday GitHub workflow, accessibility regression checker, theme-button state description, and a buyer wording-retest guide. It ran the rolling analysis on the committed recent-price slice, ran the accessibility and rendered-page structure checks, and tested the smoke checker against the local service. It did not invent buyer-retest outcomes or claim a public deployment that had not been verified. The project author remains responsible for reviewing and submitting these changes.

## Addendum 13: public wording and final document rebuild

OpenAI Codex simplified the Today summary cards, replaced the purple stronger-signal accent with the established green system colour, redesigned Explore's Colombo-Dambulla difference panel, and renamed Method to How it works with public-facing explanations of the evidence, limits and sources. It updated the proposal, technical report, two-page summary, readiness checklist, demonstration script and related README text to match the current interface and 86-test result. It rebuilt and visually reviewed the three submission PDFs. The public deployment URL and video remain unclaimed until they are genuinely completed, and the project author remains responsible for the final submission.

## Addendum 14: local-language interface

OpenAI Codex added a persistent English, Sinhala and Tamil selector to the welcome page and a compact selector on the remaining pages. It translated the core welcome, navigation, source, safety, status and Today-summary wording while deliberately preserving official item names, market names, dates and numerical values. It also replaced the informal "may rise / may fall" count with a neutral expected-direction summary, applied the established green treatment consistently to all four summary cards, added regression tests and checked the rendered Sinhala and Tamil layouts. The project author remains responsible for reviewing the translations with native speakers before public submission.

