"""
Spot checks: values quoted in the narrative on page 1 of each report (read by a
human from the PDFs) must equal what the table extractor assigns to that market.
This verifies the column-to-market mapping independently of the table itself.

Run:  SAMPLES_DIR=samples python3 test_extract_prices.py     (or pytest)
Needs the sample PDFs (not committed; see README) and pdfplumber.
"""
import os
from pathlib import Path

from extract_prices import parse_pdf

SAMPLES = Path(os.environ.get("SAMPLES_DIR", "samples"))

# (report date, item, price_type, market, prior, today) -- from each report's narrative
CASES = [
    ("2026-10-02", "Beans", "retail", "Pettah", 650, 600),
    ("2026-10-02", "Beans", "retail", "Dambulla", 580, 480),
    ("2026-10-02", "Carrot", "retail", "Pettah", 250, 300),
    ("2026-10-02", "Brinjal", "retail", "Dambulla", 285, 255),
    ("2026-10-02", "Thalapath", "wholesale", "Peliyagoda", 2000, 2300),
    ("2026-10-02", "Thalapath", "wholesale", "Negombo", 1700, 1850),
    ("2026-10-02", "Linna", "wholesale", "Peliyagoda", 830, 700),
    ("2026-10-02", "Linna", "wholesale", "Negombo", 850, 750),
    ("2026-10-02", "Potato (Local)", "retail", "Dambulla", 205, 235),
    ("2026-10-05", "Cabbage", "retail", "Dambulla", 255, 285),        # vs last Friday
    ("2026-10-05", "Green Chilli", "retail", "Pettah", 300, 350),
    ("2026-10-05", "Lime", "retail", "Dambulla", 980, 1180),
    ("2026-10-05", "Salaya", "wholesale", "Peliyagoda", 700, 350),
    ("2026-10-05", "Salaya", "wholesale", "Negombo", 650, 400),
    ("2026-10-06", "Cabbage", "retail", "Pettah", 350, 400),
    ("2026-10-06", "Brinjal", "retail", "Dambulla", 255, 325),
    ("2026-10-06", "Kelawalla", "wholesale", "Peliyagoda", 1700, 1300),
    ("2026-10-06", "Hurulla", "wholesale", "Peliyagoda", 700, 750),
    ("2026-10-07", "Tomato", "retail", "Pettah", 650, 600),
    ("2026-10-07", "Tomato", "retail", "Dambulla", 505, 455),
    ("2026-10-07", "Lime", "retail", "Pettah", 800, 1000),
    ("2026-10-07", "Big Onion (Local)", "retail", "Dambulla", 215, 245),
    ("2026-10-08", "Salaya", "wholesale", "Peliyagoda", 400, 300),
    ("2026-10-08", "Salaya", "wholesale", "Negombo", 400, 320),
    ("2026-10-08", "Banana (Sour)", "retail", "Dambulla", 160, 150),
    ("2026-10-09", "Lime", "retail", "Pettah", 1000, 1100),
    ("2026-10-09", "Lime", "retail", "Dambulla", 1080, 1255),
    ("2026-10-09", "Salaya", "wholesale", "Negombo", 320, 550),
    ("2026-10-09", "Papaw", "retail", "Dambulla", 120, 85),
    ("2026-10-09", "Potato (Imp)", "retail", "Dambulla", 150, 158),
]


def load():
    rows = []
    for p in sorted(SAMPLES.glob("*price_report*.pdf")):
        r, w = parse_pdf(p)
        assert not w, w
        rows += r
    return rows


def test_narrative_values_match_table():
    rows = load()
    index = {(r["report_date"], r["item"], r["price_type"], r["market"]): r for r in rows}
    failures = []
    for d, item, ptype, market, prior, today in CASES:
        r = index.get((d, item, ptype, market))
        got = (r["price_prior"], r["price_today"]) if r else None
        if got != (prior, today):
            failures.append((d, item, ptype, market, (prior, today), got))
    assert not failures, failures


if __name__ == "__main__":
    test_narrative_values_match_table()
    print(f"OK: all {len(CASES)} narrative spot checks match the extracted table")
