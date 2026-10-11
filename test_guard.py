"""Tests for guard.py: every refusal case in the proposal's safe-failure plan, plus the boundaries."""
from datetime import date, timedelta

import pandas as pd

from guard import assess, working_days_after

LAST = date(2026, 10, 9)        # a Friday


def make(n_days=70, last=LAST, item="Lime", dambulla="ok", colombo="ok", notes="", drop_dambulla_today=False):
    dates, d = [], last
    while len(dates) < n_days:
        if d.weekday() < 5:
            dates.append(d)
        d -= timedelta(days=1)
    rows = []
    for dt in sorted(dates):
        for ptype, market, status in (("wholesale", "Dambulla", dambulla), ("retail", "Pettah", colombo)):
            is_last = dt == last
            if drop_dambulla_today and is_last and market == "Dambulla":
                continue
            st = status if is_last else "ok"
            rows.append(dict(report_date=dt, item=item, price_type=ptype, market=market,
                             price_today=None if st != "ok" else 100.0, price_today_status=st,
                             report_notes=notes if is_last else ""))
    return pd.DataFrame(rows)


def test_fresh_and_complete_is_ok():
    v = assess(make(), "Lime", today=date(2026, 10, 12))          # Monday after the Friday report
    assert v.ok and v.status == "ok"


def test_stale_boundary_three_working_days_is_allowed_four_is_not():
    assert assess(make(), "Lime", today=date(2026, 10, 14)).ok               # Wed: Mon, Tue, Wed = 3
    v = assess(make(), "Lime", today=date(2026, 10, 15))                     # Thu = 4
    assert v.status == "stale" and "4 working days" in v.reason


def test_weekends_do_not_count():
    assert working_days_after(LAST, date(2026, 10, 11)) == 0
    assert assess(make(), "Lime", today=date(2026, 10, 11)).ok


def test_holidays_can_be_excluded():
    hol = {date(2026, 10, 12), date(2026, 10, 13)}
    assert assess(make(), "Lime", today=date(2026, 10, 15), holidays=hol).ok


def test_report_listed_on_site_but_not_read_is_refused():
    v = assess(make(), "Lime", today=date(2026, 10, 12), newest_listed=date(2026, 10, 12))
    assert v.status == "report_not_read"


def test_dambulla_market_closed_is_refused():
    v = assess(make(notes="*Dambulla market was not in operation today."), "Lime", today=date(2026, 10, 12))
    assert v.status == "market_closed"


def test_fish_market_closure_does_not_block_vegetables():
    v = assess(make(notes="*Peliyagoda and Negombo fish markets were not in operation today."),
               "Lime", today=date(2026, 10, 12))
    assert v.ok


def test_missing_dambulla_price_is_refused():
    assert assess(make(dambulla="n.a."), "Lime", today=date(2026, 10, 12)).status == "no_dambulla_price"
    assert assess(make(drop_dambulla_today=True), "Lime", today=date(2026, 10, 12)).status == "no_dambulla_price"


def test_missing_colombo_price_is_refused():
    assert assess(make(colombo="n.a."), "Lime", today=date(2026, 10, 12)).status == "no_colombo_price"


def test_too_few_observations_is_refused():
    v = assess(make(n_days=30), "Lime", today=date(2026, 10, 12))
    assert v.status == "insufficient_data" and "at least 40" in v.reason


def test_weak_signal_says_no_clear_signal():
    v = assess(make(), "Lime", today=date(2026, 10, 12), signal=0.001, min_signal=0.02)
    assert v.status == "no_clear_signal"
    assert assess(make(), "Lime", today=date(2026, 10, 12), signal=0.05, min_signal=0.02).ok


def test_stale_wins_over_other_problems():
    v = assess(make(dambulla="n.a."), "Lime", today=date(2026, 10, 20))
    assert v.status == "stale"


def test_empty_table_is_refused():
    assert assess(pd.DataFrame(columns=["report_date"]), "Lime", today=LAST).status == "insufficient_data"
