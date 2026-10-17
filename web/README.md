# Price Signal web app

A website for the Price Signal model: a Flask server, a SQLite database, and a hand-built page (no build step, no CDN, nothing loaded from other sites).

```
cards.csv ──┐                         ┌─ GET /api/status
            ├─ build_db.py ─ price_signal.db ─ server.py ─┼─ GET /api/cards?series=...
prices_all.csv (optional, history) ─┘                     ├─ GET /api/items/<item>?series=...
                                                          └─ GET /  (static/index.html)
```

The Streamlit dashboard (`app.py`) is untouched and still works.

## Run it

From the repo root:

```bash
python3 -m pip install -r web/requirements.txt
python3 web/server.py          # open http://127.0.0.1:5000
```

If port 5000 is already in use (common on macOS), choose another port:

```bash
PORT=5124 python3 web/server.py # open http://127.0.0.1:5124
```

The first start builds `web/price_signal.db` from `cards.csv`. After the daily pipeline writes a new `cards.csv`, rebuild:

```bash
python3 web/build_db.py        # uses ../cards.csv and, if present, ../prices_all.csv for price history
```

`prices_all.csv` is git-ignored. A fresh clone uses the committed one-year slice in `data/recent_prices.csv`; copy or build `prices_all.csv` only when you need the full history.

Try the layout with invented history (clearly marked "Demo data" on the page):

```bash
python3 web/build_db.py --synthetic-history
```

## IntelliJ IDEA

1. File > Open, choose the repo folder. Install the Python plugin if IntelliJ asks (or use PyCharm).
2. File > Project Structure > SDKs / Modules: set a Python 3.9+ interpreter, then run `pip install -r web/requirements.txt` in its terminal.
3. Run > Edit Configurations > + Python: script `web/server.py`, working directory = the repo root. Run it and open http://127.0.0.1:5000.
4. Database tool window > + > Data Source > SQLite. File: `web/price_signal.db` (run the server or `build_db.py` first so the file exists). Download the driver if asked, Test Connection, OK. Tables: `cards`, `prices`, `meta`.
5. Tests: `python3 -m pytest web/test_web.py`.

## The guard

Every API response goes through `guard.py` logic at request time. A figure is returned only when all three hold:

- the latest report is at most 3 working days old (`guard.MAX_AGE_WORKING_DAYS`)
- `data/refresh_log.csv` does not list a newer report than the database holds
- the latest refresh successfully checked the Central Bank report listing
- the card's own status is `ok`

Otherwise numbers, direction, signal and price history are removed server side and only the reason is sent. A missing refresh log counts as "unknown", the same as the Streamlit app.

Environment variables: `PRICE_SIGNAL_DB`, `PRICE_SIGNAL_LOG`, `PRICE_SIGNAL_TODAY` (pin today, YYYY-MM-DD), `PRICE_SIGNAL_CARDS`, `PORT`, `FLASK_DEBUG=1`.

## Where to change things

- Look and feel: `static/app.css` (colours are variables at the top, light and dark)
- Page behaviour and charts: `static/app.js`
- Database layout: `schema.sql`; loading: `build_db.py`
- API and guard: `server.py`

## Pages

| Page | What it shows |
|---|---|
| `/` Welcome | Plain-language project introduction, independence notice and entry to the price guide |
| `/today` Today | Source health, signal summary, expected-change and uncertainty chart, strongest-signal list, filters, safe CSV export and item cards with each estimate's likely range |
| `/explore` | Past prices of one item: Dambulla wholesale against a Colombo price, the gap between them, 1 week to 1 year |
| `/report` | This week against last week for every item, biggest moves, small charts, CSV download, print to PDF |
| `/method` | The evidence, read from `results_*.txt` in the repository |
| `/help` | How to read the page, what the signals mean, what it cannot do |

Price history comes from `prices_all.csv` if present, otherwise from `data/recent_prices.csv`. With neither, the history pages say so. `python3 web/build_db.py --synthetic-history` builds invented history for layout demos; every page then shows a demo-data notice.

