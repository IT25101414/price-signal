#!/usr/bin/env python3
"""
Build web/price_signal.db from the pipeline's outputs.

    python3 web/build_db.py                        # cards from ../cards.csv; history from ../prices_all.csv, else ../data/recent_prices.csv
    python3 web/build_db.py --cards path/cards.csv --prices path/prices_all.csv
    python3 web/build_db.py --synthetic-history    # demo only: invented history, marked as such in the UI

Run it again whenever model.py writes a new cards.csv (run_daily.sh does the pipeline; this is the last step).
"""
import argparse
import csv
import math
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DEFAULT_DB = HERE / "price_signal.db"
HISTORY_DAYS = 250
DEFAULT_PRICES = ROOT / "prices_all.csv"
RECENT = ROOT / "data" / "recent_prices.csv"   # a small committed slice of the table, so a clone still has charts
SERIES_KEEP = {"wholesale Dambulla", "wholesale Pettah", "retail Pettah", "retail Narahenpita"}
NUM = ["dambulla_rs", "colombo_rs", "gap_vs_usual_pct", "expected_change_pct", "low_pct", "high_pct"]
TXT = ["direction", "signal"]


def num(v):
    try:
        return float(v) if v not in ("", None) else None
    except ValueError:
        return None


def load_cards(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"{path} has no rows")
    return rows


def insert_cards(con, rows):
    for r in rows:
        con.execute(
            "INSERT OR REPLACE INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (r["date"], r["item"], r["series"], *[num(r[c]) for c in NUM],
             r.get("direction") or None, r.get("signal") or None, r["status"], r["reason"]))


def recent_frame(path, items):
    """The last HISTORY_DAYS*1.5 calendar days of the four series we show, from the full table (prices_all.csv)."""
    import pandas as pd   # only needed for the optional history
    cols = ["report_date", "item", "price_type", "market", "price_today", "price_today_status"]
    df = pd.read_csv(path, usecols=cols, low_memory=False)
    df = df[(df["price_today_status"] == "ok") & df["price_today"].notna()]
    df["report_date"] = pd.to_datetime(df["report_date"])
    df = df[df["report_date"] >= df["report_date"].max() - pd.Timedelta(days=int(HISTORY_DAYS * 1.5))]
    df["series"] = df["price_type"] + " " + df["market"]
    df = df[df["series"].isin(SERIES_KEEP) & df["item"].isin(items)]
    df = df.drop_duplicates(["report_date", "item", "series"], keep="last").sort_values(["report_date", "item", "series"])
    return df.assign(price_rs=df["price_today"].astype(float))[["report_date", "item", "series", "price_rs"]]


def card_items(con):
    return {r[0] for r in con.execute("SELECT DISTINCT item FROM cards")}


def insert_prices(con, path):
    df = recent_frame(path, card_items(con))
    con.executemany("INSERT INTO prices VALUES (?,?,?,?)",
                    [(d.date().isoformat(), i, s, float(p)) for d, i, s, p in
                     zip(df["report_date"], df["item"], df["series"], df["price_rs"])])
    return len(df)


def insert_recent_csv(con, path):
    """The committed slice (data/recent_prices.csv: report_date,item,series,price_rs)."""
    items = card_items(con)
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [(r["report_date"], r["item"], r["series"], float(r["price_rs"])) for r in csv.DictReader(fh)
                if r["item"] in items and r["series"] in SERIES_KEEP and r["price_rs"]]
    con.executemany("INSERT OR REPLACE INTO prices VALUES (?,?,?,?)", rows)
    return len(rows)


def insert_synthetic(con, end_iso):
    """Invented prices for screenshots and demos only. The UI shows a 'demo data' notice when this is used."""
    rnd = random.Random(7)
    end = date.fromisoformat(end_iso)
    days, d = [], end
    while len(days) < HISTORY_DAYS:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    rows, wd_by_item = [], {}
    for item, series, d_rs, c_rs in con.execute(
            "SELECT item, series, dambulla_rs, colombo_rs FROM cards WHERE dambulla_rs IS NOT NULL AND colombo_rs IS NOT NULL ORDER BY item, series"):
        if item not in wd_by_item:                       # one invented Dambulla path per item, shared by its Colombo series
            wd, path = 0.0, []
            for i, day in enumerate(days):
                wd = 0.9 * wd + rnd.gauss(0, 0.03)
                frac = i / (len(days) - 1)
                path.append(d_rs * math.exp(wd - 0.2 * (1 - frac)) if frac < 1 else d_rs)
            wd_by_item[item] = path
            rows.extend((day.isoformat(), item, "wholesale Dambulla", round(v, 1)) for day, v in zip(days, path))
        wc = 0.0
        for i, day in enumerate(days):
            wc = 0.9 * wc + rnd.gauss(0, 0.015)
            frac = i / (len(days) - 1)
            drift = math.log(wd_by_item[item][i] / d_rs)
            rows.append((day.isoformat(), item, series, round(c_rs * math.exp(wc + 0.1 * drift - (0.1 * (1 - frac) if frac < 1 else 0)) if frac < 1 else c_rs, 1)))
    con.executemany("INSERT INTO prices VALUES (?,?,?,?)", rows)
    return len(rows)


def build(db=DEFAULT_DB, cards=ROOT / "cards.csv", prices=ROOT / "prices_all.csv", synthetic=False):
    rows = load_cards(cards)
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.executescript((HERE / "schema.sql").read_text(encoding="utf-8"))
    insert_cards(con, rows)
    n_prices, source = 0, "none"
    if synthetic:
        n_prices, source = insert_synthetic(con, rows[0]["date"]), "synthetic"
    elif prices and Path(prices).exists():
        n_prices, source = insert_prices(con, prices), "prices_all.csv"
    elif prices and Path(prices) == DEFAULT_PRICES and RECENT.exists():
        n_prices, source = insert_recent_csv(con, RECENT), "data/recent_prices.csv"
    card_date = max(r["date"] for r in rows)
    history_date_row = con.execute("SELECT MAX(report_date) FROM prices").fetchone()
    history_date = history_date_row[0] if history_date_row else None
    if history_date and history_date != card_date:
        con.execute("DELETE FROM prices")
        n_prices, source = 0, "withheld_date_mismatch"
    meta = {"built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "cards_file": str(Path(cards).name), "history_source": source, "history_rows": str(n_prices),
            "cards_date": card_date, "history_latest_date": history_date or ""}
    con.executemany("INSERT INTO meta VALUES (?,?)", meta.items())
    con.commit()
    con.close()
    return len(rows), n_prices, source


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--cards", default=str(ROOT / "cards.csv"))
    ap.add_argument("--prices", default=str(ROOT / "prices_all.csv"))
    ap.add_argument("--synthetic-history", action="store_true")
    a = ap.parse_args()
    n, p, src = build(a.db, a.cards, a.prices, a.synthetic_history)
    print(f"built {a.db}: {n} cards, {p} history rows (history source: {src})")
    if src == "none":
        print("note: no prices_all.csv or data/recent_prices.csv found, so there is no price history.", file=sys.stderr)
