#!/usr/bin/env python3
"""
Does the price at the source market (Dambulla wholesale) tell us where Colombo prices go next?

    python3 leadlag_check.py prices_all.csv

For each item, the source is Dambulla wholesale. The targets are Pettah wholesale, Pettah retail
and Narahenpita retail. For each target and horizon h (1, 3, 5 report days) we predict the
target's log price change from today to today+h, with two models fitted on 2020-2023 and scored
on 2024-2026 (a time split, so the future never leaks into the past):

  A  uses only the target's own recent changes (momentum / reversion)
  B  adds the source: its 1-day and 5-day change, and "gap" = how far the source price has moved
     away from its usual spread to the target (the target tends to close that gap)

Skill = 1 - (squared error of the model) / (squared error of "no change"). Positive skill means
the model beats guessing that the price will not move. "Gain" is B minus A: what the source adds.
Models are pooled across items (log changes are comparable across items).
"""
import csv
import datetime as dt
import sys
from collections import defaultdict

import numpy as np

SRC = sys.argv[1] if len(sys.argv) > 1 else "prices_all.csv"
SPLIT, MIN_COVER, WIN = dt.date(2024, 1, 1), 0.90, 60
HORIZONS = (1, 3, 5)
SOURCE = ("wholesale", "Dambulla")
TARGETS = [("wholesale", "Pettah"), ("retail", "Pettah"), ("retail", "Narahenpita")]


def norm(item):
    return item.replace("(local)", "(Local)").replace("(lmp)", "(Imp)")


series, dates = defaultdict(dict), set()
with open(SRC, encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["price_today"] and float(r["price_today"]) > 0:
            d = dt.date.fromisoformat(r["report_date"])
            series[(norm(r["item"]), r["price_type"], r["market"])][d] = float(r["price_today"])
            dates.add(d)
dates = sorted(dates)
n = len(dates)
L = {k: np.log(np.array([s.get(d, np.nan) for d in dates])) for k, s in series.items()
     if len(s) / n >= MIN_COVER}
items = sorted({k[0] for k in L if (k[0],) + SOURCE in L})


def rows_for(item, target, h):
    S, T = L[(item,) + SOURCE], L[(item,) + target]
    spread = S - T
    out = []
    for t in range(WIN + 5, n - h):
        window = spread[t - WIN:t]
        if np.isfinite(window).sum() < WIN // 2:
            continue
        x = [T[t] - T[t - 1], T[t] - T[t - 5],                       # own: 1-day, 5-day change
             S[t] - S[t - 1], S[t] - S[t - 5],                       # source: 1-day, 5-day change
             spread[t] - np.nanmean(window)]                         # gap vs usual spread
        y = T[t + h] - T[t]
        if np.all(np.isfinite(x)) and np.isfinite(y):
            out.append((x, y, dates[t], dates[t + h]))
    return out


def fit_score(rows, cols):
    X = np.array([r[0] for r in rows])[:, cols]
    y = np.array([r[1] for r in rows])
    tr = np.array([r[3] < SPLIT for r in rows])
    te = np.array([r[2] >= SPLIT for r in rows])
    A = np.hstack([X, np.ones((len(X), 1))])
    beta = np.linalg.lstsq(A[tr], y[tr], rcond=None)[0]
    err = ((A[te] @ beta - y[te]) ** 2).sum()
    zero = (y[te] ** 2).sum()
    return 1 - err / zero, beta, int(te.sum())


print(f"{len(items)} items with a Dambulla wholesale series; train to 2023, test 2024 on\n")
print(f"{'target':<22}{'h':>3} {'tests':>7} {'skill A':>9} {'skill B':>9} {'gain':>8}")
for target in TARGETS:
    for h in HORIZONS:
        rows = []
        for it in items:
            if (it,) + target in L:
                rows += rows_for(it, target, h)
        if len(rows) < 200:
            continue
        sa, _, nt = fit_score(rows, [0, 1])
        sb, beta, _ = fit_score(rows, [0, 1, 2, 3, 4])
        label = f"{target[0]} {target[1]}"
        print(f"{label:<22}{h:>3} {nt:>7} {100*sa:>8.1f}% {100*sb:>8.1f}% {100*(sb-sa):>+7.1f}")
        if h == 3:
            print(f"{'':<22}    coefficients (own1d, own5d, src1d, src5d, gap): "
                  + ", ".join(f"{b:+.2f}" for b in beta[:5]))
