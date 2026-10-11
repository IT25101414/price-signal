#!/usr/bin/env python3
"""
Price Signal dashboard (Streamlit).

    python3 model.py prices_all.csv        # writes cards.csv from the latest report
    streamlit run app.py

Reads cards.csv (written by model.py). Every card was already passed through guard.py. This page
adds one more check each time it is opened, because cards.csv can be older than the page view:
  * if the latest report is more than guard.MAX_AGE_WORKING_DAYS working days old, every number is hidden
  * if the Central Bank site listed a newer report than the one in the table, every number is hidden
  * a card the guard withheld never shows a number, only the reason

The page never says "buy" or "sell". It describes what usually happens and how uncertain that is.

Optional environment variables (used by the tests and for demos):
  PRICE_SIGNAL_CARDS   path to cards.csv         (default cards.csv)
  PRICE_SIGNAL_LOG     path to the refresh log   (default data/refresh_log.csv)
  PRICE_SIGNAL_TODAY   pretend today's date, YYYY-MM-DD
"""
import os
from datetime import date

import pandas as pd
import streamlit as st

import guard

CARDS_PATH = os.environ.get("PRICE_SIGNAL_CARDS", "cards.csv")
LOG_PATH = os.environ.get("PRICE_SIGNAL_LOG", "data/refresh_log.csv")
SERIES_ORDER = ["wholesale Pettah", "retail Pettah", "retail Narahenpita"]
STATUS_TITLE = {
    "no_clear_signal": "No clear signal",
    "insufficient_data": "Insufficient data",
    "no_colombo_price": "No Colombo price in the latest report",
    "no_dambulla_price": "No Dambulla price in the latest report",
    "market_closed": "A market was closed",
    "stale": "Data too old",
    "report_not_read": "Newest report not read",
}
SIGNAL_TEXT = {"strong": "Strong signal", "weak": "Modest signal"}
NUMBER_COLS = ["dambulla_rs", "colombo_rs", "gap_vs_usual_pct", "expected_change_pct", "low_pct", "high_pct"]


def today_date():
    v = os.environ.get("PRICE_SIGNAL_TODAY")
    return date.fromisoformat(v) if v else date.today()


def age_text(n):
    if n <= 0:
        return "published today"
    return "1 working day old" if n == 1 else f"{n} working days old"


def apply_gate(cards, today, newest_listed):
    """Return (state, message, cards). state is 'ok' or 'withheld'. When withheld, every card is
    turned into a refusal with the reason and its numbers are removed."""
    latest = date.fromisoformat(str(cards["date"].iloc[0]))
    age = guard.working_days_after(latest, today)
    reason = None
    if age > guard.MAX_AGE_WORKING_DAYS:
        reason = (f"The latest report is dated {guard.fmt(latest)}, {age} working days ago. "
                  f"Estimates are withheld after more than {guard.MAX_AGE_WORKING_DAYS}.")
        status = "stale"
    elif newest_listed is not None and newest_listed > latest:
        reason = (f"The Central Bank site lists a report dated {guard.fmt(newest_listed)}, but the newest one "
                  f"we could read is {guard.fmt(latest)}. Estimates are withheld.")
        status = "report_not_read"
    if reason is None:
        return "ok", f"Data from the report of {guard.fmt(latest)} ({age_text(age)}).", cards
    gated = cards.copy()
    gated["status"] = status
    gated["reason"] = reason
    for c in NUMBER_COLS + ["signal", "direction"]:
        if c in gated:
            gated[c] = float("nan") if c in NUMBER_COLS else ""
    return "withheld", reason, gated


def range_bar(low, exp, high):
    span = max(abs(low), abs(high), abs(exp), 1.0) * 1.15

    def pos(v):
        return 50 + 50 * v / span
    return (
        '<div style="position:relative;height:14px;background:rgba(128,128,128,.2);border-radius:7px;margin:8px 0 2px">'
        f'<div style="position:absolute;left:{pos(low):.1f}%;width:{pos(high) - pos(low):.1f}%;top:0;bottom:0;'
        'background:rgba(31,111,235,.38);border-radius:7px"></div>'
        '<div style="position:absolute;left:50%;top:-3px;bottom:-3px;width:2px;background:#888"></div>'
        f'<div style="position:absolute;left:{pos(exp):.1f}%;top:-3px;bottom:-3px;width:4px;margin-left:-2px;'
        'background:#0b6b4d;border-radius:2px"></div></div>'
        '<div style="display:flex;justify-content:space-between;font-size:.75rem;opacity:.7">'
        f'<span>-{span:.0f}%</span><span>0</span><span>+{span:.0f}%</span></div>'
    )


def gap_sentence(row):
    market = row["series"].split(" ", 1)[1]
    g = float(row["gap_vs_usual_pct"])
    if abs(g) < 1:
        return f"Dambulla sits at its usual level against {market}."
    side = "above" if g > 0 else "below"
    return (f"Against {market}, Dambulla's price is {abs(g):.0f}% {side} where it usually sits. "
            "Colombo prices have typically closed part of a gap like this within 3 report days.")


def render_card(row, show_title=True):
    ok = row["status"] == "ok"
    with st.container(border=True):
        if show_title:
            st.markdown(f"**{row['item']}** · {row['series']}")
        if not ok:
            st.markdown(f"**{STATUS_TITLE.get(row['status'], 'Withheld')}**")
            st.caption(str(row["reason"]))
            return
        c1, c2, c3 = st.columns(3)
        c1.metric("Dambulla wholesale", f"Rs {row['dambulla_rs']:.0f}/kg")
        c2.metric(row["series"].title(), f"Rs {row['colombo_rs']:.0f}/kg")
        c3.metric("Gap vs usual", f"{row['gap_vs_usual_pct']:+.0f}%")
        st.write(gap_sentence(row))
        st.markdown(f"Expected change over 3 report days: **{row['expected_change_pct']:+.1f}%**  \n"
                    f"80% range: {row['low_pct']:+.1f}% to {row['high_pct']:+.1f}%")
        st.markdown(range_bar(row["low_pct"], row["expected_change_pct"], row["high_pct"]), unsafe_allow_html=True)
        st.caption(SIGNAL_TEXT.get(row["signal"], "") + ". A range that crosses zero means the direction is uncertain.")


def main():
    st.set_page_config(page_title="Price Signal", page_icon="📈", layout="centered")
    st.markdown("<style>[data-testid='stMetricValue']{font-size:1.5rem}</style>", unsafe_allow_html=True)
    st.title("Price Signal")
    st.caption("Is a Colombo vegetable price behind Dambulla, and by how much has that gap usually closed? "
               "Statistical estimates from the Central Bank's daily price reports, not advice.")

    if not os.path.exists(CARDS_PATH):
        st.error(f"No cards file found ({CARDS_PATH}). Run `python3 model.py prices_all.csv` first.")
        return
    cards = pd.read_csv(CARDS_PATH)
    if cards.empty:
        st.error("The cards file is empty, so nothing can be shown.")
        return
    cards["reason"] = cards["reason"].fillna("")
    cards["signal"] = cards["signal"].fillna("")

    state, message, cards = apply_gate(cards, today_date(), guard.newest_listed_from_log(LOG_PATH))
    (st.success if state == "ok" else st.error)(message)

    view = st.radio("View", ["Pick an item", "All items"], horizontal=True)
    if view == "Pick an item":
        items = sorted(cards["item"].unique())
        shown = cards[cards["status"] == "ok"]
        default = items.index(shown.reindex(shown["expected_change_pct"].abs().sort_values(ascending=False).index)
                              .iloc[0]["item"]) if len(shown) else 0
        item = st.selectbox("Item", items, index=default)
        rows = cards[cards["item"] == item]
        rows = rows.set_index("series").reindex([s for s in SERIES_ORDER if s in set(rows["series"])]).reset_index()
        if rows.empty:
            st.info("No cards for this item.")
        for _, r in rows.iterrows():
            render_card(r)
    else:
        chosen = st.multiselect("Series", SERIES_ORDER, default=SERIES_ORDER)
        view_df = cards[cards["series"].isin(chosen)]
        ok = view_df[view_df["status"] == "ok"].copy()
        st.subheader(f"{len(ok)} items with an estimate, largest gap first")
        if len(ok):
            ok["abs_gap"] = ok["gap_vs_usual_pct"].abs()
            ok = ok.sort_values("abs_gap", ascending=False)
            table = pd.DataFrame({
                "Item": ok["item"], "Series": ok["series"],
                "Dambulla Rs/kg": ok["dambulla_rs"].round(0), "Colombo Rs/kg": ok["colombo_rs"].round(0),
                "Gap vs usual %": ok["gap_vs_usual_pct"].round(0),
                "Expected 3-day change %": ok["expected_change_pct"].round(1),
                "80% range low %": ok["low_pct"].round(1), "80% range high %": ok["high_pct"].round(1),
                "Signal": ok["signal"].map(SIGNAL_TEXT),
            })
            st.dataframe(table, hide_index=True)
        bad = view_df[view_df["status"] != "ok"]
        with st.expander(f"{len(bad)} withheld, with the reason"):
            if len(bad):
                st.dataframe(pd.DataFrame({
                    "Item": bad["item"], "Series": bad["series"],
                    "Why": bad["status"].map(lambda s: STATUS_TITLE.get(s, s)), "Detail": bad["reason"]}),
                    hide_index=True)

    with st.expander("How to read this"):
        st.markdown(
            "- **Gap vs usual** compares today's Dambulla price with the price in your market. It is measured against "
            "how far apart the two usually are, so a normal margin does not count as a signal.\n"
            "- **Expected change** is what the model expects your market's price to do over the next 3 report days. "
            "The **80% range** is built so that about 80% of past outcomes it had not seen fell inside it. "
            "In testing on 2024 onward it held 77 to 82% of outcomes.\n"
            "- **No clear signal** means the gap is too small for the model to have shown any skill. "
            "**Insufficient data** means too few recent days with both prices.\n"
            "- The effect is modest, it was tested on a calm period (2024 onward), and a Monday report spans a weekend.\n"
            "- Source: Central Bank of Sri Lanka, Daily Price Report. Prices are rounded to the nearest Rs 5 or 10.")


main()
