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
from datetime import date, datetime, timezone
from pathlib import Path

from flask import Flask, abort, g, jsonify, request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import guard  # noqa: E402  (the same guard the Streamlit app and the model use)
import build_db  # noqa: E402
import evidence  # noqa: E402

SERIES = ["retail Pettah", "wholesale Pettah", "retail Narahenpita"]
NUMBER_FIELDS = ["dambulla_rs", "colombo_rs", "gap_vs_usual_pct", "expected_change_pct", "low_pct", "high_pct"]


def db_path():
    return Path(os.environ.get("PRICE_SIGNAL_DB", HERE / "price_signal.db"))


def today():
    """Today's date in Sri Lanka, because the reports are dated there and a host usually runs on UTC."""
    v = os.environ.get("PRICE_SIGNAL_TODAY")
    if v:
        return date.fromisoformat(v)
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Colombo")).date()
    except Exception:  # no zoneinfo or no tz database: use a fixed UTC+05:30 offset
        from datetime import timedelta
        return (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date()


def log_path():
    return os.environ.get("PRICE_SIGNAL_LOG", str(ROOT / "data" / "refresh_log.csv"))


def ensure_db():
    p = db_path()
    if not p.exists():
        cards = Path(os.environ.get("PRICE_SIGNAL_CARDS", ROOT / "cards.csv"))
        build_db.build(p, cards, ROOT / "prices_all.csv")


# History is a record of past prices, not an estimate, so it may be shown for a card that has no clear signal.
# It is withheld for every other status (a missing or closed market, too little data, anything not understood).
HISTORY_STATUSES = ("ok", "no_clear_signal")
WEEK = 5                    # report days in "this week" and in "last week"
RANGES = (5, 22, 65, 130, 250)


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
        if st != "ok":
            app.logger.warning("withholding all estimates: %s", reason)
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

    def card_for(item, series):
        return conn().execute("SELECT * FROM cards WHERE item = ? AND series = ?", (item, series)).fetchone()

    def history_block(item, series):
        """(state, reason) for showing past prices of one item and series. state 'ok' means they may be shown."""
        rd = report_date()
        st, reason, _ = gate(rd)
        if st != "ok":
            return st, reason
        row = card_for(item, series)
        if row is None:
            abort(404, f"no card for {item} / {series}")
        if row["status"] not in HISTORY_STATUSES:
            return "withheld", row["reason"]
        return "ok", f"Based on the {guard.fmt(rd)} report."

    def series_arg():
        series = request.args.get("series", SERIES[0])
        if series not in SERIES:
            abort(400, f"series must be one of {SERIES}")
        return series

    @app.get("/explore")
    def page_explore():
        return app.send_static_file("explore.html")

    @app.get("/report")
    def page_report():
        return app.send_static_file("report.html")

    @app.get("/method")
    def page_method():
        return app.send_static_file("method.html")

    @app.get("/help")
    def page_help():
        return app.send_static_file("help.html")

    @app.get("/api/items")
    def api_items():
        """Item names with, per series, whether past prices may be shown. No prices here."""
        rd = report_date()
        st, reason, _ = gate(rd)
        out = {}
        for r in conn().execute("SELECT item, series, status FROM cards ORDER BY item"):
            out.setdefault(r["item"], {})[r["series"]] = (st == "ok" and r["status"] in HISTORY_STATUSES)
        return jsonify(state=st, reason=reason, report_date=rd.isoformat(), series=SERIES, ranges=list(RANGES),
                       history_source=meta().get("history_source", "none"),
                       items=[dict(item=k, history=v) for k, v in out.items()])

    @app.get("/api/history")
    def api_history():
        item, series = request.args.get("item", ""), series_arg()
        try:
            days = int(request.args.get("days", 22))
        except ValueError:
            abort(400, "days must be a whole number")
        if days not in RANGES:
            abort(400, f"days must be one of {list(RANGES)}")
        st, reason = history_block(item, series)
        base = dict(state=st, reason=reason, item=item, series=series, days=days,
                    history_source=meta().get("history_source", "none"), dates=[], dambulla=[], colombo=[])
        if st != "ok":
            return jsonify(base)
        rows = conn().execute(
            "SELECT report_date, series, price_rs FROM prices WHERE item = ? AND series IN (?, 'wholesale Dambulla') "
            "ORDER BY report_date", (item, series)).fetchall()
        by = {}
        for r in rows:
            by.setdefault(r["report_date"], {})[r["series"]] = r["price_rs"]
        dates = sorted(by)[-days:]
        base.update(dates=dates, dambulla=[by[d].get("wholesale Dambulla") for d in dates],
                    colombo=[by[d].get(series) for d in dates])
        return jsonify(base)

    def weekly(series):
        """This week (the last 5 report days) against last week (the 5 before), for every item that may show history."""
        rd = report_date()
        st, reason, _ = gate(rd)
        out = dict(state=st, reason=reason, series=series, report_date=rd.isoformat(), items=[],
                   history_source=meta().get("history_source", "none"), this_week=None, last_week=None)
        if st != "ok":
            return out
        allowed = {r["item"] for r in conn().execute("SELECT item, status FROM cards WHERE series = ?", (series,))
                   if r["status"] in HISTORY_STATUSES}
        dates = [r["d"] for r in conn().execute(
            "SELECT DISTINCT report_date AS d FROM prices WHERE series = ? ORDER BY d", (series,))]
        if len(dates) < 2 * WEEK:
            return out
        this_w, last_w = dates[-WEEK:], dates[-2 * WEEK:-WEEK]
        out["this_week"], out["last_week"] = [this_w[0], this_w[-1]], [last_w[0], last_w[-1]]
        by = {}
        for r in conn().execute("SELECT report_date, item, series, price_rs FROM prices WHERE series IN (?, 'wholesale Dambulla') "
                                "AND report_date >= ?", (series, last_w[0])):
            by.setdefault(r["item"], {}).setdefault(r["series"], {})[r["report_date"]] = r["price_rs"]

        def avg(d, days):
            v = [d[x] for x in days if x in d]
            return sum(v) / len(v) if len(v) >= 3 else None

        for item in sorted(allowed & set(by)):
            dd, cc = by[item].get("wholesale Dambulla", {}), by[item].get(series, {})
            row = dict(item=item)
            for key, d in (("dambulla", dd), ("colombo", cc)):
                a, b = avg(d, last_w), avg(d, this_w)
                row[key] = dict(last=a, this=b, change_pct=(100 * (b / a - 1)) if a and b else None,
                                spark=[d.get(x) for x in last_w + this_w])
            if row["dambulla"]["this"] is not None or row["colombo"]["this"] is not None:
                out["items"].append(row)
        return out

    @app.get("/api/weekly")
    def api_weekly():
        return jsonify(weekly(series_arg()))

    @app.get("/api/weekly.csv")
    def api_weekly_csv():
        w = weekly(series_arg())
        if w["state"] != "ok":
            abort(409, w["reason"])
        lines = ["item,series,dambulla_last_week_rs,dambulla_this_week_rs,dambulla_change_pct,"
                 "colombo_last_week_rs,colombo_this_week_rs,colombo_change_pct"]
        f = lambda v, d=1: "" if v is None else f"{v:.{d}f}"
        for r in w["items"]:
            d, c = r["dambulla"], r["colombo"]
            lines.append(",".join([f'"{r["item"]}"', f'"{w["series"]}"', f(d["last"]), f(d["this"]), f(d["change_pct"]),
                                   f(c["last"]), f(c["this"]), f(c["change_pct"])]))
        body = "\n".join(lines) + "\n"
        return app.response_class(body, mimetype="text/csv", headers={
            "Content-Disposition": f'attachment; filename="price-signal-weekly-{w["series"].replace(" ", "-")}-{w["report_date"]}.csv"'})

    @app.get("/api/summary")
    def api_summary():
        """How many cards are in each state, and why. Counts and reasons only, never prices."""
        rd = report_date()
        st, reason, _ = gate(rd)
        counts = {}
        for r in conn().execute("SELECT status, COUNT(*) AS n FROM cards GROUP BY status"):
            counts[r["status"]] = r["n"]
        total = sum(counts.values())
        return jsonify(state=st, reason=reason, report_date=rd.isoformat(), report_date_label=guard.fmt(rd),
                       total=total, by_status=counts)

    @app.get("/api/evidence")
    def api_evidence():
        return jsonify(evidence.build(ROOT))

    @app.after_request
    def headers(resp):
        # Answers depend on today's date and the refresh log, so a cache must never replay an old one.
        if request.path.startswith("/api/") or request.path == "/healthz":
            resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(503)
    def err(e):
        return jsonify(error=e.description), e.code

    return app


app = create_app() if __name__ != "__main__" else None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    create_app().run(host="127.0.0.1", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
