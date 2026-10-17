"""
Tests for the dashboard (app.py), run with Streamlit's own test harness.

    python3 -m pytest test_app.py -q

They check the promises in the proposal: every number comes with the data date, stale or unread
data hides every number, a card the guard withheld never shows a number, and the page never says
"buy" or "sell".
"""
import re
from datetime import date

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

COLS = ["date", "item", "series", "dambulla_rs", "colombo_rs", "gap_vs_usual_pct", "expected_change_pct",
        "low_pct", "high_pct", "direction", "signal", "status", "reason"]


def cards_csv(tmp_path):
    rows = [
        ["2026-10-09", "Cabbage", "retail Pettah", 255, 450, 53.3, 10.2, -4.0, 26.5, "up", "strong", "ok", "fine"],
        ["2026-10-09", "Cabbage", "wholesale Pettah", 255, 400, -27.9, -9.0, -35.9, 29.3, "down", "weak", "ok", "fine"],
        # withheld, but the row still carries numbers: the page must not show them
        ["2026-10-09", "Carrot", "retail Pettah", 160, 250, -17.0, -4.2, -27.3, 26.3, "down", "weak",
         "no_clear_signal", "the Dambulla-to-Colombo gap is too small for the model to say anything"],
        ["2026-10-09", "Lime", "retail Pettah", "", "", "", "", "", "", "", "",
         "insufficient_data", "only 12 recent report days have both prices for Lime; at least 40 are needed"],
    ]
    p = tmp_path / "cards.csv"
    pd.DataFrame(rows, columns=COLS).to_csv(p, index=False)
    return p


def run(tmp_path, monkeypatch, today="2026-10-12", listed=None, refresh_status=None, cards=True):
    monkeypatch.setenv("PRICE_SIGNAL_CARDS", str(cards_csv(tmp_path) if cards else tmp_path / "missing.csv"))
    log = tmp_path / "refresh_log.csv"
    if listed or refresh_status:
        log.write_text(f"newest_listed,status,message\n{listed or ''},{refresh_status or 'ok'},test\n")
    monkeypatch.setenv("PRICE_SIGNAL_LOG", str(log))
    monkeypatch.setenv("PRICE_SIGNAL_TODAY", today)
    at = AppTest.from_file("app.py", default_timeout=30)
    at.run()
    assert not at.exception
    return at


def all_text(at):
    parts = []
    for group in (at.markdown, at.caption, at.success, at.error, at.info, at.warning, at.title, at.subheader):
        parts += [str(e.value) for e in group]
    parts += [str(m.value) + " " + str(m.label) for m in at.metric]
    return "\n".join(parts)


def test_fresh_data_shows_date_age_and_numbers(tmp_path, monkeypatch):
    at = run(tmp_path, monkeypatch)
    assert any("9 Oct 2026" in s.value and "working day" in s.value for s in at.success)
    assert not at.error
    assert len(at.metric) >= 3
    assert "Expected change over the 3 report days after 2026-10-09" in all_text(at)


def test_stale_data_hides_every_number(tmp_path, monkeypatch):
    at = run(tmp_path, monkeypatch, today="2026-10-20")
    assert any("working days ago" in e.value for e in at.error)
    assert len(at.metric) == 0
    text = all_text(at)
    assert "Expected change over 3 report days" not in text and "Data too old" in text


def test_newer_report_on_site_hides_every_number(tmp_path, monkeypatch):
    at = run(tmp_path, monkeypatch, listed="2026-10-12")
    assert any("12 Oct 2026" in e.value for e in at.error)
    assert len(at.metric) == 0


def test_source_failure_hides_every_number(tmp_path, monkeypatch):
    at = run(tmp_path, monkeypatch, refresh_status="source_unavailable")
    assert any("could not check" in e.value for e in at.error)
    assert len(at.metric) == 0


def test_withheld_card_shows_reason_and_no_numbers(tmp_path, monkeypatch):
    at = run(tmp_path, monkeypatch)
    at.selectbox[0].select("Carrot").run()
    assert not at.exception
    assert len(at.metric) == 0
    text = all_text(at)
    assert "No clear signal" in text and "too small for the model" in text
    assert not re.search(r"-4\.2|-27\.3|26\.3", text)


def test_insufficient_data_card_gives_reason(tmp_path, monkeypatch):
    at = run(tmp_path, monkeypatch)
    at.selectbox[0].select("Lime").run()
    assert "Insufficient data" in all_text(at) and len(at.metric) == 0


def test_all_items_view_lists_ok_cards_and_withheld_reasons(tmp_path, monkeypatch):
    at = run(tmp_path, monkeypatch)
    at.radio[0].set_value("All items").run()
    assert not at.exception
    assert "2 items with an estimate" in all_text(at)
    assert len(at.dataframe) == 2          # the estimates table and the withheld list


def test_missing_cards_file_is_an_error_not_a_crash(tmp_path, monkeypatch):
    at = run(tmp_path, monkeypatch, cards=False)
    assert any("No cards file" in e.value for e in at.error)


@pytest.mark.parametrize("today", ["2026-10-12", "2026-10-20"])
def test_page_never_says_buy_or_sell(tmp_path, monkeypatch, today):
    at = run(tmp_path, monkeypatch, today=today)
    for r in ("Pick an item", "All items"):
        at.radio[0].set_value(r).run()
        text = all_text(at).lower()
        assert not re.search(r"\b(buy|sell|purchase)\b", text), r
