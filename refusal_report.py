#!/usr/bin/env python3
"""
Refusal report: one row per way the system must say "no", with the verdict the guard actually gave.

    python3 refusal_report.py              # prints the table and writes results_refusal.txt
    python3 refusal_report.py --no-write   # print only

Each case builds a small synthetic price table (see test_guard.make) with exactly one thing wrong, so the
expected answer is known in advance. Exit status is 1 if any case does not match, so CI fails loudly.
These are tests of the guard's logic on constructed data, not a claim about any real report.
"""
import sys
from datetime import date

import pandas as pd

import guard
from test_guard import LAST, make

MON, THU = date(2026, 10, 12), date(2026, 10, 15)       # LAST is Friday 9 Oct 2026


def case(name, expected, **kw):
    table = kw.pop("table", None)
    if table is None:
        table = make(**kw.pop("make", {}))
    v = guard.assess(table, "Lime", holidays=kw.pop("holidays", frozenset()), **kw)
    return name, expected, v.status, v.reason


CASES = [
    lambda: case("Fresh, complete data", "ok", today=MON),
    lambda: case("Latest report 4 working days old", "stale", today=THU),
    lambda: case("Site lists a newer report than the table holds", "report_not_read", today=MON, newest_listed=date(2026, 10, 12)),
    lambda: case("Colombo (Pettah) market closed that day", "market_closed", today=MON, make=dict(notes="Pettah market was not in operation")),
    lambda: case("Dambulla market closed that day", "market_closed", today=MON, make=dict(notes="Dambulla market was not in operation")),
    lambda: case("Dambulla price reported as n.a.", "no_dambulla_price", today=MON, make=dict(dambulla="n.a.")),
    lambda: case("Dambulla row missing from the latest report", "no_dambulla_price", today=MON, make=dict(drop_dambulla_today=True)),
    lambda: case("Colombo price reported as n.a.", "no_colombo_price", today=MON, make=dict(colombo="n.a.")),
    lambda: case("Too few recent days with both prices (30 of 40 needed)", "insufficient_data", today=MON, make=dict(n_days=30)),
    lambda: case("Empty price table", "insufficient_data", today=MON, table=pd.DataFrame(columns=make().columns)),
    lambda: case("Gap too small for the model to have shown skill", "no_clear_signal", today=MON, signal=0.01, min_signal=0.05),
    lambda: case("4 working days old, but one is a listed public holiday", "ok", today=THU, holidays=frozenset({date(2026, 10, 13)})),
]


def main(argv):
    rows = [c() for c in CASES]
    w = max(len(r[0]) for r in rows)
    lines = [f"{'Case':<{w}}  {'Expected':<18}  {'Guard said':<18}  Result"]
    lines.append("-" * len(lines[0]))
    bad = 0
    for name, exp, got, _ in rows:
        ok = exp == got
        bad += not ok
        lines.append(f"{name:<{w}}  {exp:<18}  {got:<18}  {'PASS' if ok else 'FAIL'}")
    lines.append("")
    lines.append(f"{len(rows) - bad} of {len(rows)} refusal cases behave as specified.")
    lines.append("Synthetic tables with one deliberate fault each; see refusal_report.py and test_guard.py.")
    text = "\n".join(lines)
    print(text)
    if "--no-write" not in argv:
        with open("results_refusal.txt", "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
