"""Tests for the web server: the guard must hold on every route. Run: python3 -m pytest web/test_web.py"""
import csv
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build_db  # noqa: E402
import server  # noqa: E402

NUMBERS = server.NUMBER_FIELDS + ["direction", "signal"]


@pytest.fixture()
def make_client(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    build_db.build(db, HERE.parent / "cards.csv", prices=None, synthetic=True)
    monkeypatch.setenv("PRICE_SIGNAL_DB", str(db))
    monkeypatch.setenv("PRICE_SIGNAL_LOG", str(tmp_path / "missing_log.csv"))

    def make(today, log_newest=None):
        monkeypatch.setenv("PRICE_SIGNAL_TODAY", today)
        if log_newest:
            log = tmp_path / "log.csv"
            log.write_text(f"run_at_utc,newest_listed\n2026-10-13T00:00:00,{log_newest}\n")
            monkeypatch.setenv("PRICE_SIGNAL_LOG", str(log))
        return server.create_app().test_client()
    return make


def has_numbers(card):
    return any(card[f] is not None for f in NUMBERS)


def test_fresh_gives_numbers_only_for_ok_cards(make_client):
    d = make_client("2026-10-13").get("/api/cards").get_json()
    assert d["state"] == "ok"
    ok = [c for c in d["cards"] if c["status"] == "ok"]
    assert ok and all(c["expected_change_pct"] is not None for c in ok)
    for c in d["cards"]:
        if c["status"] != "ok":
            assert not has_numbers(c), c


@pytest.mark.parametrize("today,expect", [("2026-10-13", "ok"), ("2026-10-14", "ok"), ("2026-10-15", "stale")])
def test_age_boundary(make_client, today, expect):
    # the report is Friday 9 Oct 2026: Mon 12, Tue 13, Wed 14 are working days 1 to 3; Thu 15 is day 4
    assert make_client(today).get("/api/status").get_json()["state"] == expect


def test_stale_strips_every_number_and_history(make_client):
    c = make_client("2026-10-20")
    d = c.get("/api/cards").get_json()
    assert d["state"] == "stale"
    assert all(x["status"] == "stale" and not has_numbers(x) for x in d["cards"])
    item = c.get("/api/items/Cabbage").get_json()
    assert not has_numbers(item["card"]) and item["history"] == []


def test_unread_newer_report_withholds(make_client):
    c = make_client("2026-10-13", log_newest="2026-10-12")
    d = c.get("/api/cards").get_json()
    assert d["state"] == "report_not_read"
    assert all(not has_numbers(x) for x in d["cards"])


def test_withheld_card_has_no_history(make_client):
    c = make_client("2026-10-13")
    item = c.get("/api/items/Lime").get_json()          # no_clear_signal in cards.csv
    assert item["card"]["status"] != "ok" and item["history"] == []


def test_ok_card_has_history(make_client):
    item = make_client("2026-10-13").get("/api/items/Cabbage").get_json()
    assert item["card"]["status"] == "ok" and len(item["history"]) > 50
    assert item["history_source"] == "synthetic"


def test_bad_inputs(make_client):
    c = make_client("2026-10-13")
    assert c.get("/api/cards?series=nope").status_code == 400
    assert c.get("/api/items/Nothing").status_code == 404
    assert c.get("/healthz").get_json() == {"ok": True}
    assert b"Price Signal" in c.get("/").data


def test_db_matches_csv(tmp_path):
    db = tmp_path / "x.db"
    n, _, _ = build_db.build(db, HERE.parent / "cards.csv", prices=None)
    with open(HERE.parent / "cards.csv", newline="") as fh:
        assert n == len(list(csv.DictReader(fh)))
