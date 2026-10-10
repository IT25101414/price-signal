#!/usr/bin/env python3
"""
Can a simple model tell lasting price jumps from short-lived ones better than a naive rule?

    pip3 install --user scikit-learn
    python3 model_check.py prices_all.csv

Event = a day-over-day price jump of at least 15% in a well-covered series.
Label = "persisted" if, 5 report days later, the price has NOT given back at least half of
the jump (the same definition as jump_check.py).

Features use only what was known on the jump day: jump size and direction, recent volatility,
how many jumps the series had lately, how far the price sat from its 20-day average, whether
other markets / other items moved the same way the same day, month, and whether it is a Monday
(Monday reports compare with Friday).

Split by TIME: train on jumps whose 5-day look-ahead ended before 2024-01-01, test on jumps from
2024-01-01 onward. Random splits would leak the future into the past.
"""
import csv
import datetime as dt
import math
import sys
from collections import defaultdict

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SRC = sys.argv[1] if len(sys.argv) > 1 else "prices_all.csv"
JUMP, H, MIN_COVER, MOVE = 0.15, 5, 0.90, 0.05
SPLIT = dt.date(2024, 1, 1)


def norm(item):
    return item.replace("(local)", "(Local)").replace("(lmp)", "(Imp)")


series, dates = defaultdict(dict), set()
with open(SRC, encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["price_today"]:
            d = dt.date.fromisoformat(r["report_date"])
            series[(norm(r["item"]), r["price_type"], r["market"])][d] = float(r["price_today"])
            dates.add(d)
dates = sorted(dates)
n = len(dates)
keys = [k for k, s in series.items() if len(s) / n >= MIN_COVER]
P = {k: np.array([series[k].get(d, np.nan) for d in dates]) for k in keys}
CH = {}
with np.errstate(divide="ignore", invalid="ignore"):
    for k in keys:
        c = np.full(n, np.nan)
        c[1:] = (P[k][1:] - P[k][:-1]) / P[k][:-1]
        CH[k] = c
allch = np.vstack([CH[k] for k in keys])
with np.errstate(invalid="ignore"):
    valid = (~np.isnan(allch)).sum(axis=0)
    up_n = (allch >= MOVE).sum(axis=0)
    down_n = (allch <= -MOVE).sum(axis=0)
by_item = defaultdict(list)
for k in keys:
    by_item[k[0]].append(k)

X, y, when_start, when_end = [], [], [], []
for k in keys:
    p, c = P[k], CH[k]
    for i in range(22, n - H):
        p0, p1, ph = p[i - 1], p[i], p[i + H]
        if np.isnan(p0) or np.isnan(p1) or np.isnan(ph) or abs(c[i]) < JUMP:
            continue
        sign = 1 if c[i] > 0 else -1
        prev = c[i - 20:i]
        vol = np.nanstd(prev) if np.isfinite(prev).sum() > 3 else 0.0
        recent = int((np.abs(np.nan_to_num(c[i - 10:i])) >= JUMP).sum())
        since = 30
        for back in range(1, 31):
            if i - back > 0 and abs(np.nan_to_num(c[i - back])) >= JUMP:
                since = back
                break
        win = p[i - 21:i - 1]
        level = p0 / np.nanmean(win) - 1 if np.isfinite(win).sum() > 3 else 0.0
        same_all = ((up_n[i] if sign > 0 else down_n[i]) - 1) / max(valid[i] - 1, 1)
        others = [kk for kk in by_item[k[0]] if kk != k]
        same_item = (sum(1 for kk in others if sign * np.nan_to_num(CH[kk][i]) >= MOVE) / len(others)
                     if others else 0.0)
        m = dates[i].month
        X.append([abs(c[i]), 1.0 if sign > 0 else 0.0, vol, recent, since, level,
                  same_all, same_item, 1.0 if dates[i].weekday() == 0 else 0.0,
                  math.sin(2 * math.pi * m / 12), math.cos(2 * math.pi * m / 12)])
        gave_back = (p1 - ph) / (p1 - p0)
        y.append(1 if gave_back < 0.5 else 0)                 # 1 = persisted
        when_start.append(dates[i])
        when_end.append(dates[i + H])

X, y = np.nan_to_num(np.array(X, dtype=float)), np.array(y)
tr = np.array([e < SPLIT for e in when_end])
te = np.array([s >= SPLIT for s in when_start])
names = ["abs_jump", "is_up", "volatility", "recent_jumps", "days_since_jump", "level_vs_20d",
         "breadth_all", "same_item_agree", "is_monday", "month_sin", "month_cos"]
print(f"{len(keys)} series, {len(y)} jumps: {tr.sum()} train (to 2023), {te.sum()} test (2024 on)")
base = y[tr].mean() if y[tr].mean() >= 0.5 else 1 - y[tr].mean()
print(f"Test: {100*y[te].mean():.0f}% of jumps persisted. "
      f"Always guessing the majority class from training: {100*accuracy_score(y[te], np.full(te.sum(), int(y[tr].mean() >= 0.5))):.1f}% accuracy")
print()


def report(name, model, cols):
    model.fit(X[tr][:, cols], y[tr])
    prob = model.predict_proba(X[te][:, cols])[:, 1]
    pred = (prob >= 0.5).astype(int)
    conf = np.abs(prob - 0.5)
    order = np.argsort(-conf)
    line = (f"{name:<28} acc {100*accuracy_score(y[te], pred):4.1f}%  "
            f"AUC {roc_auc_score(y[te], prob):.3f}  Brier {brier_score_loss(y[te], prob):.3f}")
    for frac in (0.3, 0.5):
        top = order[: int(len(order) * frac)]
        line += f"  | most confident {int(frac*100)}%: {100*accuracy_score(y[te][top], pred[top]):4.1f}%"
    print(line)
    return model


report("size only (logistic)", make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)), [0, 1])
lr = report("all features (logistic)", make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
            list(range(len(names))))
report("all features (grad. boosting)", HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05,
                                                                        max_iter=200, random_state=0),
       list(range(len(names))))
print()
print("Logistic coefficients (standardised; + means more likely to persist):")
coefs = lr[-1].coef_[0]
for j in np.argsort(-np.abs(coefs)):
    print(f"  {names[j]:<18} {coefs[j]:+.3f}")
