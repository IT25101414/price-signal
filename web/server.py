#!/usr/bin/env python3
"""
Price Signal web server: Flask + SQLite + a static page.

    python3 web/server.py            # http://127.0.0.1:5000

The guard runs on every request. A number leaves this server only when the data are current
(at most guard.MAX_AGE_WORKING_DAYS working days old), no newer report is known to be unread,
and the individual card's status is "ok". Otherwise the API sends the reason and no figures.

Environment:
  PRICE_SIGNAL_DB     path to the SQLite file (default web/price_signal.db, built on first start)
  PRICE_SIGNAL_LOG    refresh log for the newest-listed check (default data/refresh_log.csv)
  PRICE_SIGNAL_TODAY  pin "today" as YYYY-MM-DD (tests and screenshots)
  PRICE_SIGNAL_CARDS  cards.csv to build the DB from if it does not exist yet
"""
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

from flask import Flask, abort, g, jsonify, request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import guard  # noqa: E402  (the same guard the Streamlit app and the model use)
import build_db  # noqa: E402

SERIES = ["retail Pettah", "wholesale Pettah", "retail Narahenpita"]
NUMBER_FIELDS = ["dambulla_rs", "colombo_rs", "gap_vs_usual_pct", "expected_change_pct", "low_pct", "high_pct"]


def db_path():
    return Path(os.environ.get("PRICE_SIGNAL_DB", HERE / "price_signal.db"))


def today():
    v = os.environ.get("PRICE_SIGNAL_TODAY")
    return date.fromisoformat(v) if v else date.today()


def log_path():
    return os.environ.get("PRICE_SIGNAL_LOG", str(ROOT / "data" / "refresh_log.csv"))


def ensure_db():
    p = db_path()
    if not p.exists():
        cards = Path(os.environ.get("PRICE_SIGNAL_CARDS", ROOT / "cards.csv"))
        build_db.build(p, cards, ROOT / "prices_all.csv")


def gate(report_date):
    """(status, reason, age) for the whole page. status 'ok' means numbers may be shown."""
    age = guard.working_days_after(report_date, today())
    if age > guard.MAX_AGE_WORKING_DAYS:
        return ("stale", f"The latest report is dated {guard.fmt(report_date)}, {age} working days ago. "
                         f"Estimates are withheld after more than {guard.MAX_AGE_WORKING_DAYS}.", age)
    listed = guard.newest_listed_from_log(log_path())
    if listed is not None and listed > report_date:
        return ("report_not_read", f"The CBSL site lists a report dated {guard.fmt(listed)}, but the newest one "
                                   f"read here is {guard.fmt(report_date)}. Estimates are withheld.", age)
    return ("ok", f"Based on the {guard.fmt(report_date)} report.", age)


def create_app():
    app = Flask(__name__, static_folder=str(HERE / "static"), static_url_path="/static")
    ensure_db()

    def conn():
        if "db" not in g:
            g.db = sqlite3.connect(f"file:{db_path()}?mode=ro", uri=True)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close(_):
        c = g.pop("db", None)
        if c is not None:
            c.close()

    def report_date():
        row = conn().execute("SELECT MAX(report_date) AS d FROM cards").fetchone()
        if not row or not row["d"]:
            abort(503, "The database has no cards. Run: python3 web/build_db.py")
        return date.fromisoformat(row["d"])

    def meta():
        return {r["key"]: r["value"] for r in conn().execute("SELECT key, value FROM meta")}

    def public_card(row, page_status, page_reason):
        c = dict(row)
        c["report_date"] = c["report_date"]
        if page_status != "ok":
            c["status"], c["reason"] = page_status, page_reason
        if c["status"] != "ok":
            for f in NUMBER_FIELDS + ["direction", "signal"]:
                c[f] = None
        return c

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/healthz")
    def healthz():
        return jsonify(ok=True)

    @app.get("/api/status")
    def api_status():
        rd = report_date()
        st, reason, age = gate(rd)
        m = meta()
        return jsonify(state=st, reason=reason, report_date=rd.isoformat(), report_date_label=guard.fmt(rd),
                       age_working_days=age, max_age_working_days=guard.MAX_AGE_WORKING_DAYS,
                       today=today().isoformat(), built_at_utc=m.get("built_at_utc"),
                       history_source=m.get("history_source", "none"), series=SERIES)

    @app.get("/api/cards")
    def api_cards():
        series = request.args.get("series", SERIES[0])
        if series not in SERIES:
            abort(400, f"series must be one of {SERIES}")
        rd = report_date()
        st, reason, _ = gate(rd)
        rows = conn().execute("SELECT * FROM cards WHERE series = ? ORDER BY item", (series,)).fetchall()
        return jsonify(state=st, reason=reason, series=series, report_date=rd.isoformat(),
                       cards=[public_card(r, st, reason) for r in rows])

    @app.get("/api/items/<path:item>")
    def api_item(item):
        series = request.args.get("series", SERIES[0])
        if series not in SERIES:
            abort(400, f"series must be one of {SERIES}")
        rd = report_date()
        st, reason, _ = gate(rd)
        row = conn().execute("SELECT * FROM cards WHERE item = ? AND series = ?", (item, series)).fetchone()
        if row is None:
            abort(404, f"no card for {item} / {series}")
        card = public_card(row, st, reason)
        history = []
        if card["status"] == "ok":       # a withheld card shows no prices at all, history included
            history = [dict(r) for r in conn().execute(
                "SELECT report_date, series, price_rs FROM prices WHERE item = ? AND series IN (?, 'wholesale Dambulla') "
                "ORDER BY report_date", (item, series))]
        return jsonify(card=card, history=history, history_source=meta().get("history_source", "none"))

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(503)
    def err(e):
        return jsonify(error=e.description), e.code

    return app


app = create_app() if __name__ != "__main__" else None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    create_app().run(host="127.0.0.1", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
