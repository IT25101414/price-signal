#!/usr/bin/env python3
"""
Decision backtest: what is the Dambulla signal worth to a buyer, as a share of purchase value?

    python3 decision_backtest.py prices_all.csv [--h 3]
    python3 decision_backtest.py --selftest

Needs robust_check.py in the same folder (it reuses its data loading and models).

The decision (kept deliberately simple and stated plainly):
  A buyer must buy an item once, either TODAY or at a deadline h report days later.
  Buying today costs p(t); waiting costs p(t+h). The model predicts the log price change
  over those h days; the buyer follows it:
      predicted rise  >= threshold  -> buy today
      predicted fall  <= -threshold -> wait
      otherwise                     -> "no clear signal": buy today (the default habit)
  The threshold is set from the TRAINING period only (to 2023), as a quantile of the
  absolute predicted change, so "act only on the strongest X% of calls" never looks at 2024+.

What is reported (test period 2024 onward, per Colombo series):
  * cost relative to always buying today, in % of the purchase value (negative = cheaper)
  * the same for always waiting, and for hindsight (the best of the two each time: a ceiling)
  * policy C: follows the model that uses only the price's OWN history
  * policy D: follows the model that also uses Dambulla
  * the number that matters: D minus C, with a 95% interval from resampling whole months
  * hit rate: on acted days, how often the direction was right (ties excluded)
"""
import sys

import numpy as np
import pandas as pd

import robust_check as rc

COVERAGES = (0.25, 0.5, 1.0)       # act on the strongest 25%, 50% or all calls
N_BOOT = 2000


def build_panel(series, target, items, h):
    frames = []
    for item in items:
        y, s = series[(item,) + target], series[(item,) + rc.SOURCE]
        f = rc.features(y, s, h)
        f["item"] = item
        f["p_now"] = np.exp(y)
        frames.append(f)
    p = pd.concat(frames)
    need = sorted({c for cols in rc.FEATS.values() for c in cols}) + ["target", "date_end", "p_now"]
    return p.dropna(subset=need)


def policy_cost(pred, thr, p_now, p_wait):
    """Cost in the item's reported unit. Wait on a predicted fall; otherwise buy today."""
    wait = pred <= -thr
    return np.where(wait, p_wait, p_now), wait


def run_one(series, target, items, h, rng):
    p = build_panel(series, target, items, h)
    tr = p[(p["date"] <= rc.TRAIN_END) & (p["date_end"] <= rc.TRAIN_END)]
    te = p[p["date"] > rc.TRAIN_END]
    if len(tr) < rc.MIN_TRAIN_ROWS or len(te) < rc.MIN_TEST_ROWS:
        return None
    p_now = te["p_now"].to_numpy()
    chg = te["target"].to_numpy()
    p_wait = p_now * np.exp(chg)
    months = te["date"].dt.to_period("M").to_numpy()
    preds_tr, preds_te = {}, {}
    for k in ("C", "D"):
        cols = rc.FEATS[k]
        m = rc.fit_ridge(tr[cols].to_numpy(), tr["target"].to_numpy())
        preds_tr[k] = rc.predict(m, tr[cols].to_numpy())
        preds_te[k] = rc.predict(m, te[cols].to_numpy())

    rel = lambda cost: (cost - p_now) / p_now                  # share of purchase value
    base = {"always wait": p_wait, "hindsight best": np.minimum(p_now, p_wait)}
    rows = []
    for name, cost in base.items():
        rows.append(dict(policy=name, share="-", rel=rel(cost).mean(), hit=np.nan))
    blocks = pd.unique(months)
    idx = {m: np.where(months == m)[0] for m in blocks}
    out = {"rows": rows, "n": len(te), "diffs": {}}
    for cov in COVERAGES:
        res = {}
        for k in ("C", "D"):
            thr = 0.0 if cov >= 1 else np.quantile(np.abs(preds_tr[k]), 1 - cov)
            cost, wait = policy_cost(preds_te[k], thr, p_now, p_wait)
            acted = (np.abs(preds_te[k]) >= thr) if cov < 1 else np.ones(len(p_now), bool)
            moved = acted & (chg != 0)
            hit = (np.sign(preds_te[k][moved]) == np.sign(chg[moved])).mean() if moved.any() else np.nan
            res[k] = (cost, acted, hit)
            rows.append(dict(policy=f"follow model {k} ({'own history' if k == 'C' else 'with Dambulla'})",
                             share=f"{100 * acted.mean():.0f}% acted" if cov < 1 else "all calls",
                             rel=rel(cost).mean(), hit=hit))
        d = rel(res["D"][0]) - rel(res["C"][0])
        blk = np.array([[d[i].sum(), len(i)] for i in idx.values()])
        boots = []
        for _ in range(N_BOOT):
            pick = rng.integers(0, len(blk), len(blk))
            s = blk[pick].sum(0)
            boots.append(s[0] / s[1])
        lo, hi = np.percentile(boots, [2.5, 97.5])
        out["diffs"][cov] = (d.mean(), lo, hi)
    return out


def run(df, h=3, quiet=False):
    axis, series = rc.build_series(df)
    rng = np.random.default_rng(0)
    results = {}
    for target in rc.TARGETS:
        items = rc.eligible_items(series, target)
        if len(items) < 3:
            continue
        r = run_one(series, target, items, h, rng)
        if r is None:
            continue
        results[target] = r
        if quiet:
            continue
        print(f"\n=== {target[0]} {target[1]}   horizon {h} report days   {r['n']} decisions in the test period ===")
        print(f"{'policy':<34}{'acted':>11}{'cost vs buy-today':>20}{'hit rate':>10}")
        print(f"{'always buy today':<34}{'-':>11}{'0.00%':>20}{'-':>10}")
        for row in r["rows"]:
            if row["policy"].startswith("follow model C"):
                print()
            hit = "-" if np.isnan(row["hit"]) else f"{100 * row['hit']:.0f}%"
            print(f"{row['policy']:<34}{row['share']:>11}{100 * row['rel']:>19.2f}%{hit:>10}")
        for cov, (dm, lo, hi) in r["diffs"].items():
            lab = "all calls" if cov >= 1 else f"strongest {int(100 * cov)}%"
            print(f"  Dambulla vs own-history model, {lab:<14}: {100 * dm:+.3f} pts of purchase value "
                  f"[{100 * lo:+.3f}, {100 * hi:+.3f}]   "
                  f"({'cheaper' if hi < 0 else 'not shown to differ' if lo <= 0 <= hi else 'dearer'})")
    if not quiet:
        print("\nNegative = cheaper than always buying today. 'hindsight best' is a ceiling no real buyer can reach.")
        print("CBSL items use different reported units, so no mixed-unit rupee total is shown. Decisions on consecutive")
        print("days overlap; treat the intervals (resampled by month) as the honest guide, not the point estimates.")
    return results


def selftest():
    ok = True
    for follower in (True, False):
        res = run(rc.synthetic(follower), h=3, quiet=True)
        verdicts = []
        for target, r in res.items():
            dm, lo, hi = r["diffs"][1.0]
            verdicts.append("cheaper" if hi < 0 else "same" if lo <= 0 <= hi else "dearer")
        want = "cheaper" if follower else "same"
        good = len(verdicts) == 3 and all(v == want for v in verdicts)
        ok &= good
        print(f"synthetic world where Colombo {'FOLLOWS' if follower else 'does NOT follow'} Dambulla: "
              f"{verdicts} -> {'OK' if good else 'FAIL'}")
    print("selftest", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    h = 3
    if "--h" in args:
        i = args.index("--h"); h = int(args[i + 1]); del args[i:i + 2]
    if len(args) != 1:
        sys.exit(__doc__)
    run(rc.load(args[0]), h=h)
