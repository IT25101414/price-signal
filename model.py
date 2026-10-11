#!/usr/bin/env python3
"""
Model module: today's Dambulla-to-Colombo gap, the expected price change, and an interval.

    python3 model.py prices_all.csv                     # live cards for the latest report -> cards.csv
    python3 model.py prices_all.csv --evaluate          # does the 80% interval really cover ~80%?
    python3 model.py --selftest                         # synthetic worlds with a known answer

Needs robust_check.py and guard.py in the same folder.

How it works (the same model robust_check.py and decision_backtest.py tested):
  * ridge regression on log price changes over the next h report days, one model per Colombo
    series (wholesale Pettah, retail Pettah, retail Narahenpita), pooled across items
  * inputs: own recent changes, distance from own 20-day mean, Dambulla changes, and the
    Dambulla-minus-Colombo gap against its own trailing 60-day average
  * interval: split-conformal. Residuals are measured on a CALIBRATION period the model was not
    fitted on, scaled by each item's recent volatility, and the 80% quantile gives the interval.
  * signal: "weak" and "strong" cut-offs are the 50% and 75% quantiles of the absolute predictions
    on the training period. Below the weak cut-off the guard says "no clear signal".
  * every card is passed through guard.assess(); a card only shows numbers when the guard says ok.

Two modes:
  --evaluate  fit to 2022, calibrate on 2023, test on 2024 onward (never seen). Prints the share of
              test outcomes inside the interval, which the proposal says should be 75-85%.
  live        fit up to one year before the latest report, calibrate on the last year, predict today.
"""
import math
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

import guard
import robust_check as rc

H = 3
NOMINAL = 0.80
THRESH_Q = (0.5, 0.75)         # weak / strong signal cut-offs (quantiles of training |prediction|)
VOL_FLOOR = 0.005
MIN_CAL_ROWS = 200
COLS = rc.FEATS["D"]
EVAL_FIT_END, EVAL_CAL_START, EVAL_CAL_END = (pd.Timestamp("2022-12-31"), pd.Timestamp("2023-01-01"),
                                              pd.Timestamp("2023-12-31"))


def build_panel(series, target, items, h):
    frames = []
    for item in items:
        y, s = series[(item,) + target], series[(item,) + rc.SOURCE]
        f = rc.features(y, s, h)
        f["item"] = item
        f["p_colombo"] = np.exp(y)
        f["p_dambulla"] = np.exp(s)
        f["vol"] = y.diff().rolling(20, min_periods=10).std().clip(lower=VOL_FLOOR)
        frames.append(f)
    return pd.concat(frames)


def fit_and_calibrate(panel, h, fit_end, cal_start, cal_end):
    need = COLS + ["target", "date_end", "vol"]
    q = panel.dropna(subset=need)
    tr = q[(q["date"] <= fit_end) & (q["date_end"] <= fit_end)]
    cal = q[(q["date"] >= cal_start) & (q["date"] <= cal_end) & (q["date_end"] <= cal_end)]
    if len(tr) < rc.MIN_TRAIN_ROWS or len(cal) < MIN_CAL_ROWS:
        return None
    m = rc.fit_ridge(tr[COLS].to_numpy(), tr["target"].to_numpy())
    scores = np.abs(cal["target"].to_numpy() - rc.predict(m, cal[COLS].to_numpy())) / (cal["vol"].to_numpy() * math.sqrt(h))
    n = len(scores)
    k = min(n, math.ceil((n + 1) * NOMINAL))               # finite-sample conformal correction
    qhat = float(np.sort(scores)[k - 1])
    abs_pred = np.abs(rc.predict(m, tr[COLS].to_numpy()))
    thr = {"weak": float(np.quantile(abs_pred, THRESH_Q[0])), "strong": float(np.quantile(abs_pred, THRESH_Q[1]))}
    return dict(model=m, qhat=qhat, thr=thr, n_train=len(tr), n_cal=n, panel=q)


def evaluate(df, h=H, quiet=False):
    axis, series = rc.build_series(df)
    out = []
    if not quiet:
        print(f"{'series':<22}{'tests':>7}{'inside 80% interval':>22}{'avg half-width':>16}  by year")
    for target in rc.TARGETS:
        items = rc.eligible_items(series, target)
        if len(items) < 3:
            continue
        fc = fit_and_calibrate(build_panel(series, target, items, h), h, EVAL_FIT_END, EVAL_CAL_START, EVAL_CAL_END)
        if fc is None:
            continue
        te = fc["panel"][fc["panel"]["date"] > EVAL_CAL_END]
        if len(te) < rc.MIN_TEST_ROWS:
            continue
        pred = rc.predict(fc["model"], te[COLS].to_numpy())
        half = fc["qhat"] * te["vol"].to_numpy() * math.sqrt(h)
        inside = np.abs(te["target"].to_numpy() - pred) <= half
        yrs = te["date"].dt.year.to_numpy()
        by_year = " ".join(f"{y}:{100 * inside[yrs == y].mean():.0f}%" for y in sorted(set(yrs)))
        res = dict(target=target, n=len(te), coverage=inside.mean(), half_width=float(np.mean(np.expm1(half))), by_year=by_year)
        out.append(res)
        if not quiet:
            print(f"{target[0] + ' ' + target[1]:<22}{len(te):>7}{100 * inside.mean():>21.1f}%{100 * res['half_width']:>15.1f}%  {by_year}")
    if not quiet:
        print("\nNominal 80%. The proposal's target is 75 to 85%. Half-width is the average +/- range for a 3-report-day change.")
    return out


def live(df, gdf, h=H, today=None, newest_listed=None):
    axis, series = rc.build_series(df)
    latest = axis[-1]
    today = today or date.today()
    rows = []
    for target in rc.TARGETS:
        items = rc.eligible_items(series, target)
        if len(items) < 3:
            continue
        p = build_panel(series, target, items, h)
        fc = fit_and_calibrate(p, h, latest - pd.Timedelta(days=366), latest - pd.Timedelta(days=365), latest)
        if fc is None:
            continue
        for item in items:
            r = p[(p["item"] == item) & (p["date"] == latest)]
            card = dict(date=latest.date().isoformat(), item=item, series=f"{target[0]} {target[1]}",
                        dambulla_rs=np.nan, colombo_rs=np.nan, gap_vs_usual_pct=np.nan, expected_change_pct=np.nan,
                        low_pct=np.nan, high_pct=np.nan, direction="", signal="", status="", reason="")
            have = len(r) == 1 and not r[COLS].isna().any(axis=None)
            pred = float("nan")
            if have:
                row = r.iloc[0]
                pred = float(rc.predict(fc["model"], r[COLS].to_numpy())[0])
                half = fc["qhat"] * float(row["vol"]) * math.sqrt(h)
                card.update(dambulla_rs=round(float(row["p_dambulla"]), 1), colombo_rs=round(float(row["p_colombo"]), 1),
                            gap_vs_usual_pct=round(100 * math.expm1(float(row["gapdev"])), 1))
            v = guard.assess(gdf, item, target=target, today=today, newest_listed=newest_listed,
                             signal=None if math.isnan(pred) else pred, min_signal=fc["thr"]["weak"])
            card["status"], card["reason"] = v.status, v.reason
            if v.ok and have:
                card.update(expected_change_pct=round(100 * math.expm1(pred), 1),
                            low_pct=round(100 * math.expm1(pred - half), 1), high_pct=round(100 * math.expm1(pred + half), 1),
                            direction="up" if pred > 0 else "down",
                            signal="strong" if abs(pred) >= fc["thr"]["strong"] else "weak")
            rows.append(card)
    return pd.DataFrame(rows)


def to_guard_frame(df):
    g = df.copy()
    g["report_date"] = pd.to_datetime(g["report_date"]).dt.date
    if "report_notes" not in g:
        g["report_notes"] = ""
    return g


def show(cards):
    ok = cards[cards["status"] == "ok"].copy()
    ok["abs"] = ok["expected_change_pct"].abs()
    print(f"report date {cards['date'].iloc[0]}; {len(ok)} cards with numbers, {len(cards) - len(ok)} withheld")
    if len(ok):
        print(f"{'item':<20}{'series':<20}{'Dambulla':>9}{'Colombo':>9}{'vs usual':>9}   expected 3-day change [80% range]   signal")
        for _, c in ok.sort_values("abs", ascending=False).iterrows():
            print(f"{c['item']:<20}{c['series']:<20}{c['dambulla_rs']:>9.0f}{c['colombo_rs']:>9.0f}{c['gap_vs_usual_pct']:>+8.1f}%"
                  f"   {c['expected_change_pct']:>+6.1f}%  [{c['low_pct']:+.1f}, {c['high_pct']:+.1f}]   {c['signal']}")
    bad = cards[cards["status"] != "ok"]
    if len(bad):
        print("withheld by the guard:", dict(bad["status"].value_counts()))


def selftest():
    ok = True
    for follower in (True, False):
        df = rc.synthetic(follower)
        res = evaluate(df, quiet=True)
        cov = [r["coverage"] for r in res]
        good = len(res) == 3 and all(0.72 <= c <= 0.88 for c in cov)
        gdf = to_guard_frame(df.assign(price_today_status="ok"))
        cards = live(df, gdf, today=date(2026, 10, 12))
        share_ok = (cards["status"] == "ok").mean()          # about half by design: the weak cut-off is the median signal
        sane = (len(cards) == 24 and 0.3 <= share_ok <= 0.8 and (cards[cards["status"] != "ok"]["reason"] != "").all()
                and (cards.dropna(subset=["low_pct"]).eval("low_pct < expected_change_pct < high_pct")).all())
        ok &= good and sane
        print(f"synthetic world where Colombo {'FOLLOWS' if follower else 'does NOT follow'} Dambulla: interval coverage "
              f"{[round(100 * c) for c in cov]}% (want 72 to 88), live cards sane: {sane} -> {'OK' if good and sane else 'FAIL'}")
    print("selftest", "PASSED" if ok else "FAILED")
    return ok


def main(argv):
    if argv == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    h, out, args = H, "cards.csv", list(argv)
    if "--h" in args:
        i = args.index("--h"); h = int(args[i + 1]); del args[i:i + 2]
    if "--out" in args:
        i = args.index("--out"); out = args[i + 1]; del args[i:i + 2]
    do_eval = "--evaluate" in args
    args = [a for a in args if a != "--evaluate"]
    if len(args) != 1:
        sys.exit(__doc__)
    df = rc.load(args[0])
    if do_eval:
        evaluate(df, h)
        return
    gdf = guard.load_prices(args[0])
    cards = live(df, gdf, h, newest_listed=guard.newest_listed_from_log())
    cards.to_csv(out, index=False)
    show(cards)
    print(f"written to {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
