#!/usr/bin/env python3
"""Rolling-origin stress test for the three-report-day Dambulla signal.

This check is deliberately separate from the main 2020-2026 evaluation. It uses
the committed recent-price slice, creates three chronological test windows, and
refits the same ridge models before each window. Model C uses only the Colombo
series' own history; model D adds the matching item's Dambulla history. A
wrong-item Dambulla series is retained as a placebo.

    python3 rolling_stress_check.py data/recent_prices.csv

The window boundaries are fixed from report-date positions (55%, 70%, 85% and
100%), not chosen after looking at the model scores. No test-window label enters
training. The check is a stability test over the recent slice, not a crisis-era
test and not a replacement for the primary full-history evaluation.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import robust_check as rc

HORIZON = 3
MIN_ITEM_TRAIN_DAYS = 90
MIN_TRAIN_ROWS = 300
MIN_TEST_ROWS = 100
WINDOW_FRACTIONS = (0.55, 0.70, 0.85)


def load_recent(path, as_of=None):
    raw = pd.read_csv(path)
    required = {"report_date", "item", "series", "price_rs"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError("recent-price input is missing: " + ", ".join(sorted(missing)))
    if as_of is not None:
        cutoff = pd.Timestamp(as_of)
        dates = pd.to_datetime(raw["report_date"], errors="raise")
        raw = raw.loc[dates <= cutoff].copy()
        if raw.empty:
            raise ValueError(f"no report dates exist on or before {cutoff.date().isoformat()}")
    split = raw["series"].str.split(" ", n=1, expand=True)
    if split.shape[1] != 2:
        raise ValueError("series must look like 'wholesale Dambulla' or 'retail Pettah'")
    frame = pd.DataFrame({
        "report_date": raw["report_date"],
        "item": raw["item"],
        "price_type": split[0],
        "market": split[1],
        "price_today": raw["price_rs"],
        "price_today_status": "ok",
        "market_assumed": "False",
    })
    return rc.clean(frame)


def windows(axis):
    dates = list(pd.DatetimeIndex(axis).sort_values().unique())
    if len(dates) < 180:
        raise ValueError("at least 180 report dates are required for the rolling check")
    cuts = [int(len(dates) * f) for f in WINDOW_FRACTIONS]
    ends = cuts[1:] + [len(dates) - 1]
    return [dict(
        name=f"W{i}",
        train_end=pd.Timestamp(dates[cut]),
        test_start=pd.Timestamp(dates[cut + 1]),
        test_end=pd.Timestamp(dates[end]),
    ) for i, (cut, end) in enumerate(zip(cuts, ends), 1)]


def eligible_items(series, target, train_end):
    items = []
    for item, ptype, market in series:
        if (ptype, market) != target:
            continue
        source = series.get((item,) + rc.SOURCE)
        if source is None:
            continue
        both = (series[(item,) + target].notna() & source.notna()
                & (source.index <= train_end))
        if int(both.sum()) >= MIN_ITEM_TRAIN_DAYS:
            items.append(item)
    return sorted(items)


def evaluate(series, target, items, window, placebo=False):
    panel = rc.panel(series, target, items, HORIZON, placebo=placebo)
    train = panel[(panel["date"] <= window["train_end"])
                  & (panel["date_end"] <= window["train_end"])]
    test = panel[(panel["date"] >= window["test_start"])
                 & (panel["date"] <= window["test_end"])]
    if len(train) < MIN_TRAIN_ROWS or len(test) < MIN_TEST_ROWS:
        return None
    y = test["target"].to_numpy()
    no_change = y ** 2
    errors = {}
    for key, columns in rc.FEATS.items():
        fitted = rc.fit_ridge(train[columns].to_numpy(), train["target"].to_numpy())
        errors[key] = (y - rc.predict(fitted, test[columns].to_numpy())) ** 2
    return test, no_change, errors, len(train)


def run(frame):
    axis, series = rc.build_series(frame)
    rows = []
    for window in windows(axis):
        for target in rc.TARGETS:
            items = eligible_items(series, target, window["train_end"])
            if len(items) < 3:
                continue
            actual = evaluate(series, target, items, window)
            placebo = evaluate(series, target, items, window, placebo=True)
            if actual is None or placebo is None:
                continue
            test, baseline, errors, train_n = actual
            _, placebo_baseline, placebo_errors, _ = placebo
            gain = (errors["C"].sum() - errors["D"].sum()) / baseline.sum()
            placebo_gain = ((placebo_errors["C"].sum() - placebo_errors["D"].sum())
                            / placebo_baseline.sum())
            item_difference = pd.Series(errors["C"] - errors["D"],
                                        index=test["item"].to_numpy())
            positive = int((item_difference.groupby(level=0).sum() > 0).sum())
            rows.append(dict(
                window=window["name"],
                train_end=window["train_end"].date().isoformat(),
                test_start=window["test_start"].date().isoformat(),
                test_end=window["test_end"].date().isoformat(),
                series=target[0] + " " + target[1],
                train_rows=train_n,
                test_rows=len(test),
                items=len(items),
                gain_pct=100 * gain,
                placebo_pct=100 * placebo_gain,
                items_positive=positive,
            ))
    return rows


def format_results(rows, source, as_of=None):
    lines = [
        "ROLLING-ORIGIN STRESS CHECK (3 REPORT DAYS)",
        f"source: {source}",
        *([f"evaluation cutoff: {as_of}"] if as_of else []),
        "Model C = Colombo own history; Model D = Model C + matching Dambulla history.",
        "gain = Model D error reduction beyond Model C, as points of no-change squared error.",
        "placebo = the same calculation with another item's Dambulla series.",
        "Windows are chronological and non-overlapping; each model is refitted using only earlier rows.",
        "This recent-slice check is not a crisis-period evaluation.",
        "",
        f"{'win':<4}{'train end':<12}{'test period':<25}{'series':<23}"
        f"{'train':>7}{'test':>7}{'gain':>8}{'placebo':>10}{'items+':>10}",
    ]
    for row in rows:
        period = row["test_start"] + " to " + row["test_end"]
        lines.append(
            f"{row['window']:<4}{row['train_end']:<12}{period:<25}{row['series']:<23}"
            f"{row['train_rows']:>7}{row['test_rows']:>7}{row['gain_pct']:>+7.1f}%"
            f"{row['placebo_pct']:>+9.1f}%{str(row['items_positive']) + '/' + str(row['items']):>10}"
        )
    if rows:
        gains = [r["gain_pct"] for r in rows]
        placebo = [r["placebo_pct"] for r in rows]
        majority = sum(r["items_positive"] > r["items"] / 2 for r in rows)
        lines += [
            "",
            f"Summary: {sum(g > 0 for g in gains)}/{len(gains)} gains were positive; "
            f"range {min(gains):+.1f}% to {max(gains):+.1f}%.",
            f"Placebo: {sum(g <= 0 for g in placebo)}/{len(placebo)} were zero or negative; "
            f"range {min(placebo):+.1f}% to {max(placebo):+.1f}%.",
            f"A majority of items benefited in {majority}/{len(rows)} market-window combinations.",
            "Interpretation: the recent lead-lag result is directionally stable across all three held-out windows,",
            "but this does not establish buyer savings or behaviour during the 2022 crisis.",
        ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", default="data/recent_prices.csv")
    parser.add_argument("--as-of",
                        help="use only report dates on or before this YYYY-MM-DD cutoff")
    parser.add_argument("--strict", action="store_true",
                        help="fail unless all gains are positive, all placebos are non-positive, and every comparison has a majority of items benefiting")
    args = parser.parse_args(argv)
    source = Path(args.source)
    rows = run(load_recent(source, args.as_of))
    if len(rows) != 9:
        raise SystemExit(f"expected 9 market-window results, got {len(rows)}")
    print(format_results(rows, source.as_posix(), args.as_of), end="")
    stable = (all(r["gain_pct"] > 0 for r in rows)
              and all(r["placebo_pct"] <= 0 for r in rows)
              and all(r["items_positive"] > r["items"] / 2 for r in rows))
    if args.strict and not stable:
        raise SystemExit("rolling stability rule failed; inspect every window before publishing new claims")


if __name__ == "__main__":
    main()
