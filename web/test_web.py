"""Tests for the web server: the guard must hold on every route. Run: python3 -m pytest web/test_web.py"""
import csv
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "test_cards.csv"   # a fixed 9 Oct 2026 sample, so the tests do not depend on today's cards.csv
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build_db  # noqa: E402
import server  # noqa: E402

NUMBERS = server.NUMBER_FIELDS + ["direction", "signal"]


@pytest.fixture()
def make_client(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    build_db.build(db, FIXTURE, prices=None, synthetic=True)
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


def test_source_failure_withholds_all_numbers_and_history(hist_client, tmp_path, monkeypatch):
    c = hist_client("2026-10-12")
    log = tmp_path / "source-down.csv"
    log.write_text("newest_listed,status,message\n2026-10-09,ok,up to date\n"
                   ",source_unavailable,could not reach listing\n")
    monkeypatch.setenv("PRICE_SIGNAL_LOG", str(log))
    status = c.get("/api/status").get_json()
    assert status["state"] == "source_unavailable"
    cards = c.get("/api/cards").get_json()["cards"]
    assert all(x["status"] == "source_unavailable" and not has_numbers(x) for x in cards)
    h = c.get("/api/history?item=Cabbage&series=retail%20Pettah&days=22").get_json()
    assert h["state"] == "source_unavailable" and h["dates"] == []


def test_later_source_failure_does_not_erase_known_unread_report(hist_client, tmp_path, monkeypatch):
    c = hist_client("2026-10-12")
    log = tmp_path / "known-newer-then-down.csv"
    log.write_text("newest_listed,status,message\n2026-10-12,partial,parse failed\n"
                   ",source_unavailable,could not reach listing\n")
    monkeypatch.setenv("PRICE_SIGNAL_LOG", str(log))
    status = c.get("/api/status").get_json()
    assert status["state"] == "report_not_read"


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
    n, _, _ = build_db.build(db, FIXTURE, prices=None)
    with open(FIXTURE, newline="") as fh:
        assert n == len(list(csv.DictReader(fh)))


def test_api_answers_are_never_cacheable(make_client):
    c = make_client("2026-10-14")
    for path in ("/api/status", "/api/cards", "/healthz"):
        r = c.get(path)
        assert r.headers["Cache-Control"] == "no-store"
        assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_today_is_sri_lanka_date(monkeypatch):
    import server
    monkeypatch.delenv("PRICE_SIGNAL_TODAY", raising=False)
    from datetime import datetime, timedelta, timezone
    expect = (datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)).date()
    assert abs((server.today() - expect).days) <= 1      # tolerates running across midnight


# ---------------- the pages and APIs added later: the guard must hold on every one ----------------
import evidence  # noqa: E402


@pytest.fixture()
def hist_client(tmp_path, monkeypatch):
    """A database with (invented) price history for all three Colombo series, so history routes have something to hide."""
    db = tmp_path / "h.db"
    build_db.build(db, FIXTURE, prices=None, synthetic=True)
    monkeypatch.setenv("PRICE_SIGNAL_DB", str(db))
    monkeypatch.setenv("PRICE_SIGNAL_LOG", str(tmp_path / "missing_log.csv"))

    def make(today):
        monkeypatch.setenv("PRICE_SIGNAL_TODAY", today)
        return server.create_app().test_client()
    return make


def first_card(client, series="retail Pettah", status=None):
    cards = client.get(f"/api/cards?series={series}").get_json()["cards"]
    return next(c for c in cards if status is None or c["status"] == status)


def test_pages_exist(hist_client):
    c = hist_client("2026-10-12")
    for path in ("/", "/today", "/explore", "/report", "/method", "/help"):
        r = c.get(path)
        assert r.status_code == 200 and b"<html" in r.data


def test_buyer_feedback_explanations_are_present(hist_client):
    c = hist_client("2026-10-12")
    assert b"about 8 times in 10" in c.get("/today").data
    assert b"shared report day means" in c.get("/explore").data
    assert b"A blank means" in c.get("/report").data
    assert b"Blank weekly value" in c.get("/help").data
    assert b'priceData: "Price data {date}"' in c.get("/static/common.js").data


def test_welcome_page_leads_to_today_and_states_independence(hist_client):
    body = hist_client("2026-10-12").get("/").data
    assert b'href="/today"' in body
    assert b"Not an official government service" in body
    assert b"sri-lanka-national-emblem-clean.png" in body
    assert b'id="language"' in body
    assert "සිංහල".encode() in body and "தமிழ்".encode() in body


def test_today_uses_professional_localised_direction_summary(hist_client):
    c = hist_client("2026-10-12")
    common = c.get("/static/common.js").data
    app = c.get("/static/app.js").data
    assert b"Upward: {up}" in common
    assert b"may rise" not in app and b"may fall" not in app
    assert b"PS.initLanguage()" in app


def test_history_for_an_ok_card_has_prices(hist_client):
    c = hist_client("2026-10-12")
    item = first_card(c, status="ok")["item"]
    h = c.get(f"/api/history?item={item}&series=retail%20Pettah&days=22").get_json()
    assert h["state"] == "ok" and len(h["dates"]) == 22
    assert len(h["dambulla"]) == len(h["colombo"]) == 22


def test_history_is_shown_for_no_clear_signal_but_not_for_missing_data(hist_client):
    c = hist_client("2026-10-12")
    cards = c.get("/api/cards?series=retail%20Pettah").get_json()["cards"]
    weak = next(x for x in cards if x["status"] == "no_clear_signal")
    assert c.get(f"/api/history?item={weak['item']}&series=retail%20Pettah&days=22").get_json()["state"] == "ok"
    gone = next((x for x in cards if x["status"] not in ("ok", "no_clear_signal")), None)
    if gone:
        h = c.get(f"/api/history?item={gone['item']}&series=retail%20Pettah&days=22").get_json()
        assert h["state"] == "withheld" and h["dates"] == [] and h["dambulla"] == []


def test_stale_page_hides_history_weekly_and_items(hist_client):
    c = hist_client("2026-10-30")              # far past the 3 working day limit
    item = "Carrot"
    h = c.get(f"/api/history?item={item}&series=retail%20Pettah&days=22").get_json()
    assert h["state"] == "stale" and h["dates"] == []
    w = c.get("/api/weekly?series=retail%20Pettah").get_json()
    assert w["state"] == "stale" and w["items"] == []
    assert c.get("/api/weekly.csv?series=retail%20Pettah").status_code == 409
    items = c.get("/api/items").get_json()
    assert items["state"] == "stale" and all(not any(i["history"].values()) for i in items["items"])


def test_unread_newer_report_hides_history(hist_client, tmp_path, monkeypatch):
    c = hist_client("2026-10-12")
    log = tmp_path / "log.csv"
    log.write_text("run_at_utc,newest_listed\n2026-10-13T00:00:00,2026-10-12\n")
    monkeypatch.setenv("PRICE_SIGNAL_LOG", str(log))
    h = c.get("/api/history?item=Carrot&series=retail%20Pettah&days=22").get_json()
    assert h["state"] == "report_not_read" and h["dates"] == []


def test_weekly_is_arithmetic_on_the_last_ten_report_days(tmp_path, monkeypatch):
    import sqlite3
    db = tmp_path / "w.db"
    build_db.build(db, FIXTURE, prices=None, synthetic=False)
    con = sqlite3.connect(db)
    items = [r[0] for r in con.execute("SELECT item FROM cards WHERE series='retail Pettah' AND status='ok' LIMIT 2")]
    item, incomplete = items
    days = ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02",
            "2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09"]
    for i, d in enumerate(days):
        last = i < 5
        con.execute("INSERT INTO prices VALUES (?,?,?,?)", (d, item, "wholesale Dambulla", 100.0 if last else 110.0))
        con.execute("INSERT INTO prices VALUES (?,?,?,?)", (d, item, "retail Pettah", 200.0 if last else 190.0))
        if i != 7:
            con.execute("INSERT INTO prices VALUES (?,?,?,?)", (d, incomplete, "wholesale Dambulla", 100.0 if last else 110.0))
        con.execute("INSERT INTO prices VALUES (?,?,?,?)", (d, incomplete, "retail Pettah", 200.0 if last else 190.0))
    con.commit(); con.close()
    monkeypatch.setenv("PRICE_SIGNAL_DB", str(db))
    monkeypatch.setenv("PRICE_SIGNAL_LOG", str(tmp_path / "none.csv"))
    monkeypatch.setenv("PRICE_SIGNAL_TODAY", "2026-10-12")
    w = server.create_app().test_client().get("/api/weekly?series=retail%20Pettah").get_json()
    row = next(r for r in w["items"] if r["item"] == item)
    assert w["this_week"] == ["2026-10-05", "2026-10-09"] and w["last_week"] == ["2026-09-28", "2026-10-02"]
    assert row["dambulla"]["change_pct"] == pytest.approx(10.0) and row["colombo"]["change_pct"] == pytest.approx(-5.0)
    assert row["dambulla"]["last"] == pytest.approx(100.0) and row["colombo"]["this"] == pytest.approx(190.0)
    partial = next(r for r in w["items"] if r["item"] == incomplete)
    assert partial["dambulla"]["this_n"] == 4 and partial["dambulla"]["change_pct"] is None
    assert partial["colombo"]["this_n"] == 5 and partial["colombo"]["change_pct"] == pytest.approx(-5.0)


def test_weekly_csv_has_one_row_per_item(hist_client):
    c = hist_client("2026-10-12")
    r = c.get("/api/weekly.csv?series=retail%20Pettah")
    assert r.status_code == 200 and r.mimetype == "text/csv"
    lines = r.data.decode().strip().splitlines()
    assert lines[0].startswith("item,series,") and len(lines) > 5


def test_bad_arguments_are_refused_with_json(hist_client):
    c = hist_client("2026-10-12")
    assert c.get("/api/history?item=Carrot&series=nope&days=22").status_code == 400
    assert c.get("/api/history?item=Carrot&series=retail%20Pettah&days=7").status_code == 400
    assert c.get("/api/history?item=Carrot&series=retail%20Pettah&days=x").status_code == 400
    assert c.get("/api/history?item=NoSuchThing&series=retail%20Pettah&days=22").status_code == 404
    assert "error" in c.get("/api/weekly?series=nope").get_json()


def test_summary_has_counts_and_no_prices(hist_client):
    s = hist_client("2026-10-12").get("/api/summary").get_json()
    assert s["total"] == sum(s["by_status"].values()) and s["by_status"]
    assert not any(k in s for k in server.NUMBER_FIELDS)


REPO = HERE.parent


def test_evidence_matches_the_result_files_in_the_repo():
    e = evidence.build(REPO)
    if not (REPO / "results_model.txt").exists():
        pytest.skip("no results files in this checkout")
    assert len(e["calibration"]) == 9 and len(e["gain"]) == 9 and len(e["decision"]) == 3
    assert len(e["rolling"]) == 9
    three = {r["series"]: r["inside"] for r in e["calibration"] if r["h"] == 3}
    text = (REPO / "results_model.txt").read_text()
    for series, inside in three.items():
        assert f"{inside:.1f}%" in text and series in text
    for r in e["gain"]:
        assert r["lo"] <= r["gain"] <= r["hi"]
    for r in e["decision"]:
        assert r["d_all"]["pct"] > r["hindsight_pct"]         # a real buyer cannot beat hindsight
    assert all(r["gain"] > 0 and r["placebo"] <= 0 for r in e["rolling"])


def test_method_page_mentions_buyer_sessions_and_rolling_check(hist_client):
    body = hist_client("2026-10-12").get("/method").data
    assert b"Three buyers completed short usability sessions" in body
    assert b"Does the relationship stay useful over time?" in body


def test_recent_slice_is_used_when_the_full_table_is_absent(tmp_path, monkeypatch):
    import build_db
    slice_ = tmp_path / "recent.csv"
    slice_.write_text("report_date,item,series,price_rs\n"
                      "2026-10-09,Carrot,wholesale Dambulla,200\n2026-10-09,Carrot,retail Pettah,260\n"
                      "2026-10-09,Nothing,retail Pettah,5\n2026-10-09,Carrot,fish Negombo,9\n")
    monkeypatch.setattr(build_db, "RECENT", slice_)
    monkeypatch.setattr(build_db, "DEFAULT_PRICES", tmp_path / "prices_all.csv")      # does not exist
    db = tmp_path / "s.db"
    n_cards, n_prices, source = build_db.build(db, FIXTURE, prices=tmp_path / "prices_all.csv")
    assert source == "data/recent_prices.csv" and n_prices == 2        # unknown item and unknown series are dropped


def test_history_is_withheld_when_its_latest_date_does_not_match_cards(tmp_path, monkeypatch):
    import build_db
    slice_ = tmp_path / "stale-recent.csv"
    slice_.write_text("report_date,item,series,price_rs\n"
                      "2026-10-08,Carrot,wholesale Dambulla,200\n"
                      "2026-10-08,Carrot,retail Pettah,260\n")
    monkeypatch.setattr(build_db, "RECENT", slice_)
    monkeypatch.setattr(build_db, "DEFAULT_PRICES", tmp_path / "prices_all.csv")
    db = tmp_path / "stale.db"
    _, n_prices, source = build_db.build(db, FIXTURE, prices=tmp_path / "prices_all.csv")
    assert n_prices == 0 and source == "withheld_date_mismatch"
    import sqlite3
    with sqlite3.connect(db) as con:
        assert con.execute("SELECT COUNT(*) FROM prices").fetchone()[0] == 0


def test_recent_frame_keeps_only_shown_series_and_items(tmp_path):
    import build_db
    full = tmp_path / "prices_all.csv"
    full.write_text("report_date,item,price_type,market,price_today,price_today_status\n"
                    "2026-10-08,Carrot,wholesale,Dambulla,200,ok\n"
                    "2026-10-08,Carrot,retail,Pettah,260,ok\n"
                    "2026-10-08,Carrot,retail,Pettah,265,ok\n"           # duplicate: the last one wins
                    "2026-10-08,Carrot,wholesale,Peliyagoda,90,ok\n"      # not a series we show
                    "2026-10-08,Carrot,retail,Narahenpita,,ok\n"          # no price
                    "2026-10-08,Carrot,retail,Narahenpita,300,n.a.\n"     # not an ok price
                    "2026-10-08,Fish,retail,Pettah,900,ok\n")             # not an item on the cards
    df = build_db.recent_frame(full, {"Carrot"})
    assert sorted(zip(df["series"], df["price_rs"])) == [("retail Pettah", 265.0), ("wholesale Dambulla", 200.0)]
