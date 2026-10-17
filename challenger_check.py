#!/usr/bin/env python3
"""
Challenger check: does a gradient-boosting model beat the ridge model we use?

    python3 challenger_check.py prices_all.csv        # real data
    python3 challenger_check.py --selftest            # synthetic worlds with a known answer

Same data, same split and same scoring as robust_check.py: train to 2023, test 2024 onward, scored by squared
error against "no change". Both models see the same six features (model D). The only difference is the learner:

    ridge    the model used in the product (model D)
    boosted  scikit-learn HistGradientBoostingRegressor, pooled across items, settings fixed IN ADVANCE
             (shallow trees, small learning rate, heavy regularisation). Nothing is tuned on the test period.

The number that matters is  edge = skill(boosted) - skill(ridge), with a 95% interval from resampling whole
months. Rule fixed before running: the challenger is adopted only if, for the 3-report-day target, its interval
lies above zero and the edge is at least 0.5 points in EVERY Colombo series. Otherwise the ridge model stays,
because it has fewer moving parts and every number can be explained.
"""
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import robust_check as rc

HORIZONS = (1, 3, 5)
DECISION_H = 3
MIN_EDGE = 0.005          # 0.5 percentage points of squared error vs "no change"
N_BOOT = 2000
GB_PARAMS = dict(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=100,
                 l2_regularization=1.0, random_state=0)


def compare(p):
    """Ridge D against boosted on one panel. Returns None if there is too little data."""
    tr = p[(p["date"] <= rc.TRAIN_END) & (p["date_end"] <= rc.TRAIN_END)]
    te = p[p["date"] > rc.TRAIN_END]
    if len(tr) < rc.MIN_TRAIN_ROWS or len(te) < rc.MIN_TEST_ROWS:
        return None
    cols = rc.FEATS["D"]
    yv = te["target"].to_numpy()
    sse_n = yv ** 2
    ridge = rc.fit_ridge(tr[cols].to_numpy(), tr["target"].to_numpy())
    err_r = (yv - rc.predict(ridge, te[cols].to_numpy())) ** 2
    gb = HistGradientBoostingRegressor(**GB_PARAMS).fit(tr[cols].to_numpy(), tr["target"].to_numpy())
    err_g = (yv - gb.predict(te[cols].to_numpy())) ** 2
    return te, sse_n, err_r, err_g


def boot_interval(te, sse_n, err_r, err_g, seed=0):
    rng = np.random.default_rng(seed)
    months = te["date"].dt.to_period("M").to_numpy()
    keys = pd.unique(months)
    blk = np.array([[sse_n[months == m].sum(), err_r[months == m].sum(), err_g[months == m].sum()] for m in keys])
    boots = []
    for _ in range(N_BOOT):
        s = blk[rng.integers(0, len(blk), len(blk))].sum(0)
        boots.append((s[1] - s[2]) / s[0])
    return np.percentile(boots, [2.5, 97.5])


def run(df, quiet=False):
    axis, series = rc.build_series(df)
    results = []
    if not quiet:
        print(f"{'target':<22}{'h':>2}{'tests':>7}{'ridge':>8}{'boosted':>9}{'edge':>7}{'95% CI':>16}  years (edge by year)")
    for target in rc.TARGETS:
        items = rc.eligible_items(series, target)
        if len(items) < 3:
            continue
        for h in HORIZONS:
            out = compare(rc.panel(series, target, items, h))
            if out is None:
                continue
            te, sse_n, err_r, err_g = out
            edge = (err_r.sum() - err_g.sum()) / sse_n.sum()
            lo, hi = boot_interval(te, sse_n, err_r, err_g)
            yrs = te["date"].dt.year.to_numpy()
            yr_txt = " ".join(f"{y}:{100 * (err_r[yrs == y].sum() - err_g[yrs == y].sum()) / sse_n[yrs == y].sum():+.1f}"
                              for y in sorted(set(yrs)))
            results.append(dict(target=target, h=h, edge=edge, lo=lo, hi=hi,
                                skill_ridge=1 - err_r.sum() / sse_n.sum(), skill_gb=1 - err_g.sum() / sse_n.sum()))
            if not quiet:
                r = results[-1]
                print(f"{target[0] + ' ' + target[1]:<22}{h:>2}{len(te):>7}{100 * r['skill_ridge']:>7.1f}%"
                      f"{100 * r['skill_gb']:>8.1f}%{100 * edge:>+7.1f}"
                      f"{'[' + format(100 * lo, '+.1f') + ',' + format(100 * hi, '+.1f') + ']':>16}  {yr_txt}")
    decision = decide(results)
    if not quiet:
        print("\nedge = skill(boosted) - skill(ridge), in percentage points of squared error vs 'no change'.")
        print(f"Rule (fixed in advance): adopt the challenger only if, at h={DECISION_H}, the interval is above zero and the edge")
        print(f"is at least {100 * MIN_EDGE:.1f} points in every Colombo series.")
        print(f"Decision: {decision}")
    return results, decision


def decide(results):
    rows = [r for r in results if r["h"] == DECISION_H]
    if len(rows) < 3:
        return "keep ridge (not enough series to decide)"
    if all(r["lo"] > 0 and r["edge"] >= MIN_EDGE for r in rows):
        return "ADOPT boosted"
    return "keep ridge"


# ---------------- self-test on synthetic data with a known answer ----------------
def synthetic(nonlinear, seed=3):
    """Colombo follows Dambulla. In the 'nonlinear' world it only reacts when the gap is large (a threshold)."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2021-06-01", "2026-10-09")
    markups = {("wholesale", "Pettah"): 0.0, ("retail", "Pettah"): 0.15, ("retail", "Narahenpita"): 0.3}
    rows = []
    for it in range(8):
        s = np.log(300) + np.cumsum(rng.normal(0, 0.05, len(dates)))
        series = {("wholesale", "Dambulla"): s}
        for (ptype, market), mk in markups.items():
            y = np.zeros(len(dates))
            y[0] = s[0] + mk
            for t in range(1, len(dates)):
                gap = s[t - 1] + mk - y[t - 1]
                if nonlinear:
                    resp = 0.4 * gap if abs(gap) > 0.2 else 0.0
                else:
                    resp = 0.25 * gap
                y[t] = y[t - 1] + resp + rng.normal(0, 0.01)
            series[(ptype, market)] = y
        for (ptype, market), vals in series.items():
            rows.append(pd.DataFrame({"report_date": dates, "item": f"item{it}", "price_type": ptype, "market": market,
                                      "price_today": np.round(np.exp(vals) / 5) * 5,
                                      "price_today_status": "ok", "market_assumed": "False"}))
    return rc.clean(pd.concat(rows))


def selftest():
    ok = True
    for nonlinear, want in ((False, "keep ridge"), (True, "ADOPT boosted")):
        _, decision = run(synthetic(nonlinear), quiet=True)
        good = decision == want
        ok &= good
        print(f"synthetic world with a {'THRESHOLD' if nonlinear else 'LINEAR'} response: decision '{decision}' "
              f"-> {'OK' if good else 'FAIL (wanted ' + want + ')'}")
    print("selftest", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        sys.exit(0 if selftest() else 1)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run(rc.load(sys.argv[1]))
