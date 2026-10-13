#!/usr/bin/env python3
"""
Build web/price_signal.db from the pipeline's outputs.

    python3 web/build_db.py                        # cards from ../cards.csv, history from ../prices_all.csv if present
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


def insert_prices(con, path):
    import pandas as pd   # only needed for the optional history
    cols = ["report_date", "item", "price_type", "market", "price_today", "price_today_status"]
    df = pd.read_csv(path, usecols=cols)
    df = df[(df["price_today_status"] == "ok") & df["price_today"].notna()]
    df["report_date"] = pd.to_datetime(df["report_date"])
    df = df[df["report_date"] >= df["report_date"].max() - pd.Timedelta(days=int(HISTORY_DAYS * 1.5))]
    df["series"] = df["price_type"] + " " + df["market"]
    keep = {"wholesale Dambulla", "wholesale Pettah", "retail Pettah", "retail Narahenpita"}
    df = df[df["series"].isin(keep)]
    items = {r[0] for r in con.execute("SELECT DISTINCT item FROM cards")}
    df = df[df["item"].isin(items)].drop_duplicates(["report_date", "item", "series"], keep="last")
    con.executemany("INSERT INTO prices VALUES (?,?,?,?)",
                    [(d.date().isoformat(), i, s, float(p)) for d, i, s, p in
                     zip(df["report_date"], df["item"], df["series"], df["price_today"])])
    return len(df)


def insert_synthetic(con, end_iso):
    """Invented prices for screenshots and demos only. The UI shows a 'demo data' notice when this is used."""
    rnd = random.Random(7)
    end = date.fromisoformat(end_iso)
    days, d = [], end
    while len(days) < 120:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    rows = []
    for item, d_rs, c_rs in con.execute("SELECT item, dambulla_rs, colombo_rs FROM cards WHERE series='retail Pettah' AND dambulla_rs IS NOT NULL"):
        base_d, base_c, wd, wc = d_rs, c_rs, 0.0, 0.0
        for i, day in enumerate(days):
            wd = 0.9 * wd + rnd.gauss(0, 0.03)
            wc = 0.9 * wc + 0.1 * wd + rnd.gauss(0, 0.015)
            f = math.exp
            frac = i / (len(days) - 1)
            pd_ = base_d * f(wd - 0.2 * (1 - frac)) if frac < 1 else base_d
            pc_ = base_c * f(wc - 0.1 * (1 - frac)) if frac < 1 else base_c
            rows.append((day.isoformat(), item, "wholesale Dambulla", round(pd_, 1)))
            rows.append((day.isoformat(), item, "retail Pettah", round(pc_, 1)))
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
    meta = {"built_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "cards_file": str(Path(cards).name), "history_source": source, "history_rows": str(n_prices)}
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
        print("note: no prices_all.csv found, so the detail view will have no price history.", file=sys.stderr)
