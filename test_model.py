"""Tests for model.py on synthetic data with a known answer (no real data needed)."""
from datetime import date

import numpy as np

import model
import robust_check as rc

TODAY = date(2026, 10, 12)


def _cards(follower=True, today=TODAY):
    df = rc.synthetic(follower)
    gdf = model.to_guard_frame(df.assign(price_today_status="ok"))
    return model.live(df, gdf, today=today)


def test_interval_covers_about_eighty_percent_on_unseen_data():
    for follower in (True, False):
        res = model.evaluate(rc.synthetic(follower), quiet=True)
        assert len(res) == 3
        assert all(0.72 <= r["coverage"] <= 0.88 for r in res), [r["coverage"] for r in res]


def test_cards_have_ordered_intervals_and_reasons():
    c = _cards()
    assert len(c) == 24
    shown = c[c["status"] == "ok"]
    assert len(shown) > 0
    assert (shown["low_pct"] < shown["expected_change_pct"]).all() and (shown["expected_change_pct"] < shown["high_pct"]).all()
    assert shown["signal"].isin(["weak", "strong"]).all() and shown["direction"].isin(["up", "down"]).all()
    assert np.isfinite(shown[["dambulla_rs", "colombo_rs", "gap_vs_usual_pct", "expected_change_pct",
                              "low_pct", "high_pct"]].to_numpy()).all()
    assert (c[c["status"] != "ok"]["reason"].str.len() > 0).all()


def test_weak_signals_are_withheld_not_shown():
    c = _cards()
    weak = c[c["status"] == "no_clear_signal"]
    assert len(weak) > 0
    assert weak["expected_change_pct"].isna().all() and weak["low_pct"].isna().all()


def test_stale_data_withholds_every_number():
    c = _cards(today=date(2026, 11, 20))
    assert (c["status"] == "stale").all()
    assert c["expected_change_pct"].isna().all()


def test_unseen_newer_report_withholds_every_number():
    df = rc.synthetic(True)
    gdf = model.to_guard_frame(df.assign(price_today_status="ok"))
    c = model.live(df, gdf, today=TODAY, newest_listed=date(2026, 10, 12))
    assert (c["status"] == "report_not_read").all() and c["expected_change_pct"].isna().all()


def test_source_failure_withholds_every_number():
    df = rc.synthetic(True)
    gdf = model.to_guard_frame(df.assign(price_today_status="ok"))
    c = model.live(df, gdf, today=TODAY, refresh_status="source_unavailable")
    assert (c["status"] == "source_unavailable").all() and c["expected_change_pct"].isna().all()


def test_incomplete_latest_features_never_produce_an_ok_card_without_numbers():
    df = rc.synthetic(True)
    latest = df["report_date"].max()
    prior = sorted(df["report_date"].unique())[-2]
    missing = ((df["item"] == "item0") & (df["price_type"] == "wholesale") &
               (df["market"] == "Dambulla") & (df["report_date"] == prior))
    broken = df.loc[~missing].copy()
    gdf = model.to_guard_frame(broken.assign(price_today_status="ok"))
    cards = model.live(broken, gdf, today=latest.date())
    affected = cards[cards["item"] == "item0"]
    assert len(affected) == 3 and (affected["status"] == "insufficient_data").all()
    shown = cards[cards["status"] == "ok"]
    assert np.isfinite(shown[["dambulla_rs", "colombo_rs", "gap_vs_usual_pct", "expected_change_pct",
                              "low_pct", "high_pct"]].to_numpy()).all()
