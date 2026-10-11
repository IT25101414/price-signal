#!/usr/bin/env python3
"""
The guard: decides, per item, whether the user may see an estimate, or only a reason.

    python3 guard.py prices_all.csv                 # freshness + every item with a Dambulla price
    python3 guard.py prices_all.csv Lime "Green Chilli"

Nothing in the interface may show a number unless assess() returned status "ok".

Order of checks (the first that fails wins):
  stale              latest report in the table is older than MAX_AGE_WORKING_DAYS working days
  report_not_read    the site lists a newer report than the table holds (see refresh.py)
  market_closed      the latest report's footnote says the Colombo or Dambulla market was not in operation
  no_dambulla_price  no Dambulla wholesale price in the latest report
  no_colombo_price   no price for the chosen Colombo series in the latest report
  insufficient_data  too few recent report days with BOTH prices
  no_clear_signal    the gap is too small for the model to have shown skill (needs the model)
  ok

Working days are Monday to Friday, minus any `holidays` you pass in. Sri Lankan public
holidays are not built in: a long holiday stretch can make the data look stale, and the
guard then errs on the side of refusing, which is the safe direction.
"""
import csv
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd

MAX_AGE_WORKING_DAYS = 3
WINDOW_REPORTS = 60          # look at the most recent 60 report days ...
MIN_PAIRED_OBS = 40          # ... and require at least 40 with both prices
SOURCE = ("wholesale", "Dambulla")
DEFAULT_TARGET = ("retail", "Pettah")


@dataclass
class Verdict:
    status: str
    reason: str

    @property
    def ok(self):
        return self.status == "ok"

    def __str__(self):
        return f"{self.status}: {self.reason}"


def fmt(d):
    return f"{d.day} {d.strftime('%b %Y')}"


def working_days_after(last, today, holidays=frozenset()):
    """Working days (Mon-Fri, not holidays) after `last`, up to and including `today`."""
    n, d = 0, last
    while d < today:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in holidays:
            n += 1
    return n


def _series(prices, item, ptype, market):
    s = prices[(prices["item"] == item) & (prices["price_type"] == ptype) & (prices["market"] == market)]
    return s.set_index("report_date")


def assess(prices, item, target=DEFAULT_TARGET, today=None, newest_listed=None, signal=None,
           min_signal=None, holidays=frozenset(), max_age=MAX_AGE_WORKING_DAYS,
           window=WINDOW_REPORTS, min_obs=MIN_PAIRED_OBS):
    """prices: DataFrame in the extractor's output format (report_date as datetime.date)."""
    today = today or date.today()
    if prices.empty:
        return Verdict("insufficient_data", "the price table is empty")
    latest = prices["report_date"].max()
    age = working_days_after(latest, today, holidays)
    if age > max_age:
        return Verdict("stale", f"the latest report is dated {fmt(latest)}, {age} working days ago; "
                                f"estimates are withheld after more than {max_age}")
    if newest_listed is not None and newest_listed > latest:
        return Verdict("report_not_read", f"the site lists a report dated {fmt(newest_listed)} but the newest "
                                          f"one we could read is {fmt(latest)}; estimates are withheld")
    today_rows = prices[prices["report_date"] == latest]
    notes = " ".join(str(x) for x in today_rows["report_notes"].dropna().unique())
    for market in (SOURCE[1], target[1]):
        for line in notes.split(" | "):
            if market.lower() in line.lower() and "not in operation" in line.lower():
                return Verdict("market_closed", f"the {fmt(latest)} report says the {market} market was not in operation")
    src_all, tgt_all = _series(prices, item, *SOURCE), _series(prices, item, *target)

    def has_price(s):
        if latest not in s.index:
            return False
        row = s.loc[latest]
        row = row.iloc[-1] if hasattr(row, "ndim") and row.ndim > 1 else row
        return row["price_today_status"] == "ok" and pd.notna(row["price_today"])

    if not has_price(src_all):
        return Verdict("no_dambulla_price", f"no Dambulla wholesale price for {item} in the {fmt(latest)} report")
    if not has_price(tgt_all):
        return Verdict("no_colombo_price", f"no {target[0]} {target[1]} price for {item} in the {fmt(latest)} report")
    recent = sorted(prices["report_date"].unique())[-window:]
    ok_src = set(src_all[(src_all["price_today_status"] == "ok")].index) & set(recent)
    ok_tgt = set(tgt_all[(tgt_all["price_today_status"] == "ok")].index) & set(recent)
    paired = len(ok_src & ok_tgt)
    if paired < min_obs:
        return Verdict("insufficient_data", f"only {paired} recent report days (of {len(recent)} considered) have both "
                                            f"prices for {item}; at least {min_obs} are needed")
    if signal is not None and min_signal is not None and abs(signal) < min_signal:
        return Verdict("no_clear_signal", "the Dambulla-to-Colombo gap is too small for the model to say anything")
    return Verdict("ok", f"data are current ({fmt(latest)}) and complete enough for {item}")


def load_prices(path):
    cols = ["report_date", "item", "price_type", "market", "price_today", "price_today_status", "report_notes"]
    df = pd.read_csv(path, usecols=cols, dtype={"report_notes": str})
    df["report_date"] = pd.to_datetime(df["report_date"]).dt.date
    return df


def newest_listed_from_log(log_file="data/refresh_log.csv"):
    try:
        with open(log_file, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        v = rows[-1]["newest_listed"] if rows else ""
        return datetime.strptime(v, "%Y-%m-%d").date() if v else None
    except (OSError, ValueError, KeyError):
        return None


def main(argv):
    if not argv:
        sys.exit(__doc__)
    prices = load_prices(argv[0])
    listed = newest_listed_from_log()
    items = argv[1:] or sorted(prices[(prices["price_type"] == SOURCE[0]) & (prices["market"] == SOURCE[1])]["item"].unique())
    latest = prices["report_date"].max()
    print(f"latest report in the table: {fmt(latest)}; newest listed on the site (from the refresh log): "
          f"{fmt(listed) if listed else 'unknown'}; today: {fmt(date.today())}")
    for it in items:
        print(f"  {it:<22} {assess(prices, it, newest_listed=listed)}")


if __name__ == "__main__":
    main(sys.argv[1:])
