#!/usr/bin/env python3
"""
Feasibility check for "short-lived vs lasting price swings" (stdlib only).

    python3 jump_check.py prices_all.csv

For every well-covered series, find day-over-day price jumps of at least JUMP (15%) between
consecutive report days, then look H (5) report days later. A jump "reverted" if the price
gave back at least half of the jump by then, otherwise it "persisted". Reports the shares
overall and by item. If almost everything reverts (or almost everything persists), a naive
rule already does the job and there is little for a model to add.
"""
import csv
import datetime as dt
import sys
from collections import defaultdict

SRC = sys.argv[1] if len(sys.argv) > 1 else "prices_all.csv"
JUMP, H, MIN_COVER = 0.15, 5, 0.90

def norm(item):
    return item.replace("(local)", "(Local)").replace("(lmp)", "(Imp)")

data = defaultdict(dict)
dates = set()
with open(SRC, encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["price_today"]:
            d = dt.date.fromisoformat(r["report_date"])
            data[(norm(r["item"]), r["price_type"], r["market"])][d] = float(r["price_today"])
            dates.add(d)
dates = sorted(dates)
n = len(dates)

counts = defaultdict(lambda: [0, 0])          # item -> [reverted, persisted]
by_dir = {"up": [0, 0], "down": [0, 0]}
used = 0
for (item, ptype, market), s in data.items():
    if len(s) / n < MIN_COVER:
        continue
    used += 1
    for i in range(1, n - H):
        p0, p1, ph = s.get(dates[i - 1]), s.get(dates[i]), s.get(dates[i + H])
        if p0 is None or p1 is None or ph is None or p0 <= 0:
            continue
        if abs(p1 - p0) / p0 < JUMP:
            continue
        gave_back = (p1 - ph) / (p1 - p0)       # 1 = fully reverted, 0 = stayed, <0 = kept going
        k = 0 if gave_back >= 0.5 else 1
        counts[item][k] += 1
        by_dir["up" if p1 > p0 else "down"][k] += 1

tot = [sum(v[0] for v in counts.values()), sum(v[1] for v in counts.values())]
total = sum(tot)
print(f"{used} series with >= {int(MIN_COVER*100)}% coverage; jumps >= {int(JUMP*100)}% "
      f"checked {H} report days later")
if not total:
    sys.exit("no jumps found")
print(f"{total} jumps: {100*tot[0]/total:.0f}% reverted, {100*tot[1]/total:.0f}% persisted")
for k, (a, b) in by_dir.items():
    if a + b:
        print(f"  {k:>4}: {a+b} jumps, {100*a/(a+b):.0f}% reverted")
print(f"A rule that always guesses the more common outcome is right "
      f"{100*max(tot)/total:.0f}% of the time.")
print()
print("By item (jumps, % reverted):")
for item, (a, b) in sorted(counts.items(), key=lambda kv: -(kv[1][0] + kv[1][1])):
    if a + b >= 10:
        print(f"  {item:<24} {a+b:>4}  {100*a/(a+b):>3.0f}%")
