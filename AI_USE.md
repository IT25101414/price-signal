# AI assistance disclosure (required by ModelX 2.0 rules)

| Tool | Used for |
|---|---|
| Claude (Anthropic) | Researching data sources, drafting the project proposal, writing first versions of `download_cbsl_reports.py`, `extract_prices.py` and `test_extract_prices.py`, and explaining PDF layouts. |

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

