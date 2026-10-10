#!/usr/bin/env python3
"""
Coverage report for prices_all.csv (stdlib only).

    python3 coverage.py prices_all.csv

Prints which item / price type / market series are complete enough to model, and writes
coverage.csv with one row per series: days with a price, share of all report days, first and
last date with a price, and the longest run of report days with no price.
"""
import csv
import datetime as dt
import sys
from collections import defaultdict

src = sys.argv[1] if len(sys.argv) > 1 else "prices_all.csv"

series = defaultdict(dict)          # (section, item, price_type, market) -> {date: price or None}
all_dates = set()
with open(src, encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        d = dt.date.fromisoformat(r["report_date"])
        all_dates.add(d)
        v = r["price_today"]
        series[(r["section"], r["item"], r["price_type"], r["market"])][d] = float(v) if v else None

dates = sorted(all_dates)
n_days = len(dates)
rows = []
for (section, item, ptype, market), s in series.items():
    have = [d for d in dates if s.get(d) is not None]
    longest = cur = 0
    for d in dates:
        if s.get(d) is None:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    rows.append(dict(
        section=section, item=item, price_type=ptype, market=market,
        days_with_price=len(have), pct_of_days=round(100 * len(have) / n_days, 1),
        first_price=min(have).isoformat() if have else "",
        last_price=max(have).isoformat() if have else "",
        longest_gap_days=longest))

rows.sort(key=lambda r: -r["days_with_price"])
with open("coverage.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

latest = dates[-1]
print(f"{n_days} report days, {dates[0]} to {latest} "
      f"({(dt.date.today() - latest).days} days before today)")
print(f"{len(rows)} series (item x price type x market)")
for pct in (95, 90, 75, 50):
    print(f"  with a price on >= {pct}% of days: {sum(r['pct_of_days'] >= pct for r in rows)}")
stale = [r for r in rows if r["last_price"] and r["last_price"] < latest.isoformat()]
print(f"  series whose last price is older than the latest report: {len(stale)}")
print()
print("Best covered series:")
for r in rows[:25]:
    print(f"  {r['pct_of_days']:5.1f}%  {r['item']:<22} {r['price_type']:<9} {r['market']:<12} "
          f"longest gap {r['longest_gap_days']} days")
print()
print("Wrote coverage.csv")
