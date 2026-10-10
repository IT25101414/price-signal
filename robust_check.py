#!/usr/bin/env python3
"""
Robustness check for the claim "Dambulla wholesale prices help predict Colombo prices".

    pip3 install pandas numpy
    python3 robust_check.py prices_all.csv        # real data (output of extract_prices.py)
    python3 robust_check.py --selftest            # synthetic data with a known answer

Setup (no peeking at the future):
  * target  : log price change over the next h report days for one Colombo series
              (wholesale Pettah, retail Pettah, retail Narahenpita)
  * source  : the same item's Dambulla wholesale price
  * train   : rows up to 2023-12-31 (labels that reach past it are dropped); test: 2024 onward
  * models  : ridge regressions on log changes, scored by squared error vs "no change"
        A = own recent changes
        C = A + target's distance from its own 20-day mean        (OWN-HISTORY CONTROL)
        D = C + Dambulla changes + Dambulla-minus-target gap      (WHAT DAMBULLA ADDS)
  * the number that matters is  gain = skill(D) - skill(C): what Dambulla adds BEYOND
    everything the target's own history already explains (including mean reversion).
  * gap is measured against its own trailing 60-day average, so a fixed Colombo-over-
    Dambulla markup per item cannot masquerade as a signal.
  * uncertainty: 95% interval by resampling whole months.
  * placebo: Dambulla series of a DIFFERENT item. A real item-specific lead should vanish.
"""
import sys

import numpy as np
import pandas as pd

TRAIN_END = pd.Timestamp("2023-12-31")
TARGETS = [("wholesale", "Pettah"), ("retail", "Pettah"), ("retail", "Narahenpita")]
SOURCE = ("wholesale", "Dambulla")
HORIZONS = (1, 3, 5)
RIDGE = 1.0
MIN_ITEM_TRAIN_OBS = 300
MIN_TRAIN_ROWS, MIN_TEST_ROWS = 500, 300
N_BOOT = 2000
FEATS = {
    "A": ["own1d", "own5d"],
    "C": ["own1d", "own5d", "devown"],
    "D": ["own1d", "own5d", "devown", "src1d", "src5d", "gapdev"],
}


def load(path):
    df = pd.read_csv(path, dtype={"market_assumed": str})
    return clean(df)


def clean(df):
    df = df[(df["price_today_status"] == "ok") & df["price_today"].notna() & (df["price_today"] > 0)]
    df = df[df["market_assumed"].astype(str) != "True"].copy()
    df["report_date"] = pd.to_datetime(df["report_date"])
    return df[["report_date", "item", "price_type", "market", "price_today"]]


def build_series(df):
    axis = pd.DatetimeIndex(sorted(df["report_date"].unique()))
    series = {}
    for (item, ptype, market), g in df.groupby(["item", "price_type", "market"]):
        s = g.set_index("report_date")["price_today"]
        s = s[~s.index.duplicated(keep="last")].reindex(axis)
        series[(item, ptype, market)] = np.log(s)
    return axis, series


def features(y, s, h):
    d = pd.DataFrame({"y": y, "s": s})
    f = pd.DataFrame(index=d.index)
    f["own1d"] = d.y - d.y.shift(1)
    f["own5d"] = d.y - d.y.shift(5)
    f["src1d"] = d.s - d.s.shift(1)
    f["src5d"] = d.s - d.s.shift(5)
    gap = d.s - d.y
    f["gapdev"] = gap - gap.shift(1).rolling(60, min_periods=30).mean()
    f["devown"] = d.y - d.y.shift(1).rolling(20, min_periods=10).mean()
    f["target"] = d.y.shift(-h) - d.y
    f["date"] = d.index
    f["date_end"] = pd.Series(d.index, index=d.index).shift(-h)
    return f


def fit_ridge(X, y, alpha=RIDGE):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    ym = y.mean()
    beta = np.linalg.solve(Z.T @ Z + alpha * np.eye(Z.shape[1]), Z.T @ (y - ym))
    return mu, sd, beta, ym


def predict(m, X):
    mu, sd, beta, ym = m
    return ((X - mu) / sd) @ beta + ym


def eligible_items(series, target):
    items = []
    for (item, ptype, market) in series:
        if (ptype, market) != target:
            continue
        src = series.get((item,) + SOURCE)
        if src is None:
            continue
        both = series[(item,) + target].notna() & src.notna() & (src.index <= TRAIN_END)
        if both.sum() >= MIN_ITEM_TRAIN_OBS:
            items.append(item)
    return sorted(items)


def panel(series, target, items, h, placebo=False):
    frames = []
    for k, item in enumerate(items):
        src_item = items[(k + 1) % len(items)] if placebo else item
        f = features(series[(item,) + target], series[(src_item,) + SOURCE], h)
        f["item"] = item
        frames.append(f)
    p = pd.concat(frames)
    need = sorted({c for cols in FEATS.values() for c in cols}) + ["target", "date_end"]
    return p.dropna(subset=need)


def evaluate(p):
    tr = p[(p["date"] <= TRAIN_END) & (p["date_end"] <= TRAIN_END)]
    te = p[p["date"] > TRAIN_END]
    if len(tr) < MIN_TRAIN_ROWS or len(te) < MIN_TEST_ROWS:
        return None
    yv = te["target"].to_numpy()
    sse_n = yv ** 2
    err, models = {}, {}
    for k, cols in FEATS.items():
        models[k] = fit_ridge(tr[cols].to_numpy(), tr["target"].to_numpy())
        err[k] = (yv - predict(models[k], te[cols].to_numpy())) ** 2
    return te, sse_n, err, models


def gain_of(sse_n, err):
    return (err["C"].sum() - err["D"].sum()) / sse_n.sum()


def verdict(gain, lo, placebo, n_pos, n_items):
    if lo > 0 and gain >= 0.01 and placebo < 0.5 * gain and n_pos / n_items >= 0.6:
        return "supported"
    if lo > 0 and gain > 0:
        return "partly: check placebo / items"
    return "NOT supported"


def run(df, quiet=False):
    axis, series = build_series(df)
    rng = np.random.default_rng(0)
    results = []
    if not quiet:
        print(f"{'target':<22}{'h':>2}{'tests':>7}{'skillA':>8}{'skillC':>8}{'skillD':>8}"
              f"{'gain':>7}{'95% CI':>16}{'placebo':>8}  {'years':<22}{'items+':>7}  verdict")
    for target in TARGETS:
        items = eligible_items(series, target)
        if len(items) < 3:
            continue
        for h in HORIZONS:
            ev = evaluate(panel(series, target, items, h))
            evp = evaluate(panel(series, target, items, h, placebo=True))
            if ev is None or evp is None:
                continue
            te, sse_n, err, models = ev
            gain = gain_of(sse_n, err)
            placebo = gain_of(evp[1], evp[2])
            skill = {k: 1 - err[k].sum() / sse_n.sum() for k in err}
            months = te["date"].dt.to_period("M").to_numpy()
            keys = pd.unique(months)
            idx = {m: np.where(months == m)[0] for m in keys}
            blk = np.array([[sse_n[i].sum(), err["C"][i].sum(), err["D"][i].sum()] for i in idx.values()])
            boots = []
            for _ in range(N_BOOT):
                pick = rng.integers(0, len(blk), len(blk))
                s = blk[pick].sum(0)
                boots.append((s[1] - s[2]) / s[0])
            lo, hi = np.percentile(boots, [2.5, 97.5])
            yrs = te["date"].dt.year.to_numpy()
            yr_txt = " ".join(f"{y}:{100 * (err['C'][yrs == y].sum() - err['D'][yrs == y].sum()) / sse_n[yrs == y].sum():+.1f}"
                              for y in sorted(set(yrs)))
            diff = pd.Series(err["C"] - err["D"], index=te["item"].to_numpy())
            n_pos = int((diff.groupby(level=0).sum() > 0).sum())
            n_items = diff.index.nunique()
            mu, sd, beta, _ = models["D"]
            gi = FEATS["D"].index("gapdev")
            gap_coef = beta[gi] / sd[gi]
            v = verdict(gain, lo, placebo, n_pos, n_items)
            results.append(dict(target=target, h=h, gain=gain, lo=lo, hi=hi, placebo=placebo,
                                n_pos=n_pos, n_items=n_items, gap_coef=gap_coef, verdict=v))
            if not quiet:
                print(f"{target[0] + ' ' + target[1]:<22}{h:>2}{len(te):>7}{100 * skill['A']:>7.1f}%"
                      f"{100 * skill['C']:>7.1f}%{100 * skill['D']:>7.1f}%{100 * gain:>+7.1f}"
                      f"{'[' + format(100 * lo, '+.1f') + ',' + format(100 * hi, '+.1f') + ']':>16}"
                      f"{100 * placebo:>+8.1f}  {yr_txt:<22}{n_pos:>3}/{n_items:<3}  {v}"
                      f"   (gap coef {gap_coef:+.2f})")
    if not quiet:
        print("\ngain = skill(D) - skill(C), in percentage points of squared error vs 'no change'.")
        print("gap coef: predicted log change over h days per unit of Dambulla-minus-target gap")
        print("(units: share of the unusual gap that closes within h report days).")
    return results


# ---------------- self-test on synthetic data with a known answer ----------------
def synthetic(follower, seed=1):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2021-06-01", "2026-10-09")
    rows = []
    for it in range(8):
        s = np.log(300) + np.cumsum(rng.normal(0, 0.04, len(dates)))
        markups = {("wholesale", "Pettah"): 0.0, ("retail", "Pettah"): 0.15, ("retail", "Narahenpita"): 0.3}
        series = {("wholesale", "Dambulla"): s}
        for (ptype, market), mk in markups.items():
            y = np.zeros(len(dates))
            y[0] = s[0] + mk
            c = np.log(300) + mk
            for t in range(1, len(dates)):
                if follower:        # Colombo chases yesterday's Dambulla price (error correction)
                    y[t] = y[t - 1] + 0.25 * (s[t - 1] + mk - y[t - 1]) + rng.normal(0, 0.02)
                else:               # Colombo only mean-reverts around its own level
                    y[t] = c + 0.8 * (y[t - 1] - c) + rng.normal(0, 0.05)
            series[(ptype, market)] = y
        for (ptype, market), vals in series.items():
            price = np.round(np.exp(vals) / 5) * 5
            rows.append(pd.DataFrame({"report_date": dates, "item": f"item{it}", "price_type": ptype,
                                      "market": market, "price_today": price,
                                      "price_today_status": "ok", "market_assumed": "False"}))
    return clean(pd.concat(rows))


def selftest():
    ok = True
    for follower in (True, False):
        res = run(synthetic(follower), quiet=True)
        vs = [r["verdict"] for r in res]
        want = "supported" if follower else "NOT supported"
        good = all(v == want for v in vs) and len(vs) == 9
        ok &= good
        print(f"synthetic world where Colombo {'FOLLOWS' if follower else 'does NOT follow'} Dambulla: "
              f"verdicts {sorted(set(vs))} -> {'OK' if good else 'FAIL'}   "
              f"(mean gain {100 * np.mean([r['gain'] for r in res]):+.1f} pts, "
              f"mean placebo {100 * np.mean([r['placebo'] for r in res]):+.1f} pts)")
    print("selftest", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        sys.exit(0 if selftest() else 1)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run(load(sys.argv[1]))
