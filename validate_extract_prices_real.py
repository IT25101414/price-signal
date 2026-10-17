"""
Spot checks: values quoted in the narrative on page 1 of each report (read by a
human from the PDFs) must equal what the table extractor assigns to that market.
This verifies the column-to-market mapping independently of the table itself.
NOTE: 2021 narratives quote WHOLESALE prices; from 2022 on they quote RETAIL prices
unless a market is named as wholesale (fish, Marandagahamula rice).

This is an optional validation against original source reports, deliberately kept
outside the default pytest/CI collection because the PDFs are not redistributed.

Run:  SAMPLES_DIR=samples python3 validate_extract_prices_real.py
Needs the sample PDFs (not committed; see README) and pdfplumber.
"""
import os
from pathlib import Path

from extract_prices import UnsupportedLayout, parse_pdf

SAMPLES = Path(os.environ.get("SAMPLES_DIR", "samples"))

import pytest  # noqa: E402

# The sample PDFs are not committed, so these checks run only when this file is
# invoked explicitly. The default suite has repository-owned unit tests for the
# extractor helpers and reports no environment-dependent skips.
needs_samples = pytest.mark.skipif(
    not (SAMPLES.is_dir() and any(SAMPLES.glob("*.pdf"))),
    reason="sample PDFs not present (see README); run with SAMPLES_DIR=<folder>")

R, W = "retail", "wholesale"
# (report date, item, price_type, market, prior, today)
CASES = [
    # ---- 2021 (narrative quotes wholesale prices) ----
    ("2021-06-03", "Carrot", W, "Dambulla", 145, 123),
    ("2021-06-03", "Tomato", W, "Pettah", 100, 110),
    ("2021-06-03", "Brinjal", W, "Pettah", 100, 110),
    ("2021-06-03", "Lime", W, "Pettah", 100, 120),
    ("2021-06-03", "Red Onion (Local)", W, "Dambulla", 255, 270),
    ("2021-06-04", "Beans", W, "Dambulla", 238, 135),
    ("2021-06-04", "Carrot", W, "Pettah", 130, 120),
    ("2021-06-04", "Carrot", W, "Dambulla", 123, 85),
    ("2021-06-04", "Cabbage", W, "Dambulla", 105, 135),
    ("2021-06-04", "Green Chilli", W, "Pettah", 125, 165),
    ("2021-06-04", "Lime", W, "Dambulla", 95, 155),
    ("2021-06-04", "Banana (Sour)", W, "Pettah", 60, 50),
    ("2021-06-04", "Banana (Sour)", W, "Dambulla", 28, 23),
    ("2021-06-04", "Potato (Local)", W, "Dambulla", 138, 128),
    # ---- 2022 ----
    ("2022-06-01", "Beans", R, "Pettah", 650, 600),
    ("2022-06-01", "Carrot", R, "Dambulla", 265, 335),
    ("2022-06-01", "Brinjal", R, "Dambulla", 215, 275),
    ("2022-06-01", "Nadu (Imp)", W, "Marandagahamula", 200, 216),
    ("2022-06-01", "Red Onion (Local)", R, "Dambulla", 440, 515),
    ("2022-06-01", "Potato (Local)", R, "Dambulla", 253, 275),
    ("2022-06-01", "Katta", R, "Pettah", 2300, 2500),
    # CBSL's own narrative says 600 -> 475, but its table (and the previous day's report) say 605 -> 475.
    # We follow the table, which is consistent across days. A real discrepancy inside the source.
    ("2022-06-02", "Beans", R, "Dambulla", 605, 475),
    ("2022-06-02", "Carrot", R, "Pettah", 300, 350),
    ("2022-06-02", "Green Chilli", R, "Pettah", 350, 500),
    ("2022-06-02", "Red Onion (Local)", R, "Dambulla", 515, 470),
    ("2022-06-02", "Dried Chilli (Imp)", R, "Pettah", 1700, 1800),
    ("2022-06-02", "Hurulla", W, "Peliyagoda", 1000, 1100),
    # ---- 2023 ----
    ("2023-06-01", "Carrot", R, "Pettah", 320, 350),
    ("2023-06-01", "Cabbage", R, "Dambulla", 330, 280),
    ("2023-06-01", "Tomato", R, "Dambulla", 290, 255),
    ("2023-06-01", "Green Chilli", R, "Pettah", 400, 350),
    ("2023-06-01", "Green Chilli", R, "Dambulla", 370, 320),
    ("2023-06-01", "Salaya", W, "Peliyagoda", 450, 620),
    ("2023-06-01", "Salaya", W, "Negombo", 450, 530),
    ("2023-06-01", "Red Onion (lmp)", R, "Dambulla", 365, 405),
    ("2023-06-02", "Beans", R, "Dambulla", 335, 305),
    ("2023-06-02", "Tomato", R, "Dambulla", 255, 230),
    ("2023-06-02", "Brinjal", R, "Dambulla", 320, 355),
    ("2023-06-02", "Green Chilli", R, "Pettah", 350, 400),
    ("2023-06-02", "Linna", W, "Peliyagoda", 1150, 1000),
    ("2023-06-02", "Red Onion (lmp)", R, "Dambulla", 405, 380),
    # ---- 2024 (03 June compares with last Friday) ----
    ("2024-06-03", "Beans", R, "Pettah", 750, 550),
    ("2024-06-03", "Beans", R, "Dambulla", 655, 430),
    ("2024-06-03", "Lime", R, "Pettah", 1100, 1200),
    ("2024-06-03", "Lime", R, "Dambulla", 855, 905),
    ("2024-06-03", "Tomato", R, "Dambulla", 175, 140),
    ("2024-06-03", "Brinjal", R, "Pettah", 400, 450),
    ("2024-06-03", "Brinjal", R, "Dambulla", 305, 355),
    ("2024-06-03", "Red Onion (Local)", R, "Dambulla", 415, 320),
    ("2024-06-03", "Big Onion (Imp)", R, "Dambulla", 240, 260),
    ("2024-06-04", "Beans", R, "Pettah", 550, 650),
    ("2024-06-04", "Beans", R, "Dambulla", 430, 455),
    ("2024-06-04", "Cabbage", R, "Pettah", 100, 120),
    ("2024-06-04", "Tomato", R, "Pettah", 180, 200),
    ("2024-06-04", "Brinjal", R, "Pettah", 450, 500),
    ("2024-06-04", "Brinjal", R, "Dambulla", 355, 455),
    ("2024-06-04", "Red Onion (lmp)", R, "Dambulla", 365, 395),
    ("2024-06-04", "Potato (Local)", R, "Dambulla", 260, 275),
    # ---- 2025 ----
    ("2025-06-02", "Beans", R, "Pettah", 350, 400),
    ("2025-06-02", "Beans", R, "Dambulla", 345, 405),
    ("2025-06-02", "Carrot", R, "Pettah", 650, 700),
    ("2025-06-02", "Carrot", R, "Dambulla", 670, 755),
    ("2025-06-02", "Brinjal", R, "Pettah", 450, 400),
    ("2025-06-02", "Brinjal", R, "Dambulla", 355, 305),
    ("2025-06-02", "Green Chilli", R, "Pettah", 450, 700),
    ("2025-06-02", "Green Chilli", R, "Dambulla", 395, 530),
    ("2025-06-02", "Paraw", W, "Peliyagoda", 1500, 1600),
    ("2025-06-02", "Red Onion (lmp)", R, "Pettah", 420, 450),
    ("2025-06-02", "Red Onion (lmp)", R, "Dambulla", 310, 365),
    ("2025-06-02", "Potato (Imp)", R, "Dambulla", 163, 153),
    ("2025-06-03", "Beans", R, "Dambulla", 405, 320),
    ("2025-06-03", "Carrot", R, "Dambulla", 755, 590),
    ("2025-06-03", "Tomato", R, "Dambulla", 455, 495),
    ("2025-06-03", "Green Chilli", R, "Dambulla", 530, 655),
    ("2025-06-03", "Pineapple", R, "Dambulla", 230, 205),
    ("2025-06-03", "Salaya", W, "Peliyagoda", 650, 750),
    ("2025-06-03", "Salaya", W, "Negombo", 650, 700),
    ("2025-06-03", "Potato (Imp)", R, "Dambulla", 153, 175),
    # ---- 2026 June (fish markets closed on 1 June) ----
    ("2026-06-01", "Carrot", R, "Dambulla", 335, 405),
    ("2026-06-01", "Cabbage", R, "Pettah", 130, 150),
    ("2026-06-01", "Cabbage", R, "Dambulla", 135, 230),
    ("2026-06-01", "Tomato", R, "Dambulla", 305, 370),
    ("2026-06-01", "Pumpkin", R, "Pettah", 150, 170),
    ("2026-06-01", "Pineapple", R, "Dambulla", 355, 265),
    ("2026-06-01", "Potato (Local)", R, "Pettah", 300, 347),
    ("2026-06-01", "Coconut (Avg.)", R, "Dambulla", 130, 110),
    ("2026-06-02", "Beans", R, "Dambulla", 365, 415),
    ("2026-06-02", "Carrot", R, "Pettah", 300, 350),
    ("2026-06-02", "Brinjal", R, "Pettah", 450, 500),
    ("2026-06-02", "Brinjal", R, "Dambulla", 385, 435),
    ("2026-06-02", "Green Chilli", R, "Pettah", 350, 600),
    ("2026-06-02", "Green Chilli", R, "Dambulla", 430, 555),
    ("2026-06-02", "Banana (Sour)", R, "Dambulla", 105, 95),
    ("2026-06-02", "Big Onion (Imp)", R, "Pettah", 223, 210),
    ("2026-06-02", "Coconut (Avg.)", R, "Dambulla", 110, 130),
    # ---- 2026 October ----
    ("2026-10-02", "Beans", R, "Pettah", 650, 600),
    ("2026-10-02", "Beans", R, "Dambulla", 580, 480),
    ("2026-10-02", "Carrot", R, "Pettah", 250, 300),
    ("2026-10-02", "Brinjal", R, "Dambulla", 285, 255),
    ("2026-10-02", "Thalapath", W, "Peliyagoda", 2000, 2300),
    ("2026-10-02", "Thalapath", W, "Negombo", 1700, 1850),
    ("2026-10-02", "Linna", W, "Peliyagoda", 830, 700),
    ("2026-10-02", "Linna", W, "Negombo", 850, 750),
    ("2026-10-02", "Potato (Local)", R, "Dambulla", 205, 235),
    ("2026-10-05", "Cabbage", R, "Dambulla", 255, 285),        # vs last Friday
    ("2026-10-05", "Green Chilli", R, "Pettah", 300, 350),
    ("2026-10-05", "Lime", R, "Dambulla", 980, 1180),
    ("2026-10-05", "Salaya", W, "Peliyagoda", 700, 350),
    ("2026-10-05", "Salaya", W, "Negombo", 650, 400),
    ("2026-10-06", "Cabbage", R, "Pettah", 350, 400),
    ("2026-10-06", "Brinjal", R, "Dambulla", 255, 325),
    ("2026-10-06", "Kelawalla", W, "Peliyagoda", 1700, 1300),
    ("2026-10-06", "Hurulla", W, "Peliyagoda", 700, 750),
    ("2026-10-07", "Tomato", R, "Pettah", 650, 600),
    ("2026-10-07", "Tomato", R, "Dambulla", 505, 455),
    ("2026-10-07", "Lime", R, "Pettah", 800, 1000),
    ("2026-10-07", "Big Onion (Local)", R, "Dambulla", 215, 245),
    ("2026-10-08", "Salaya", W, "Peliyagoda", 400, 300),
    ("2026-10-08", "Salaya", W, "Negombo", 400, 320),
    ("2026-10-08", "Banana (Sour)", R, "Dambulla", 160, 150),
    ("2026-10-09", "Lime", R, "Pettah", 1000, 1100),
    ("2026-10-09", "Lime", R, "Dambulla", 1080, 1255),
    ("2026-10-09", "Salaya", W, "Negombo", 320, 550),
    ("2026-10-09", "Papaw", R, "Dambulla", 120, 85),
    ("2026-10-09", "Potato (Imp)", R, "Dambulla", 150, 158),
]


def load():
    rows, rejected = [], []
    for p in sorted(SAMPLES.glob("*price_report*.pdf")):
        try:
            r, w = parse_pdf(p)
        except UnsupportedLayout as e:
            rejected.append((p.name, str(e)))
            continue
        assert not w, w
        rows += r
    return rows, rejected


@needs_samples
def test_narrative_values_match_table():
    rows, _ = load()
    index = {(r["report_date"], r["item"], r["price_type"], r["market"]): r for r in rows}
    failures = []
    for d, item, ptype, market, prior, today in CASES:
        r = index.get((d, item, ptype, market))
        got = (r["price_prior"], r["price_today"]) if r else None
        if got != (prior, today):
            failures.append((d, item, ptype, market, (prior, today), got))
    assert not failures, failures


@needs_samples
def test_2020_layout_is_rejected_not_guessed():
    _, rejected = load()
    names = [n for n, _ in rejected]
    assert all(n.startswith("2020-") for n in names), names


@needs_samples
def test_closed_fish_markets_are_flagged():
    rows, _ = load()
    june1 = [r for r in rows if r["report_date"] == "2026-06-01"]
    assert june1 and all("not in operation" in r["report_notes"] for r in june1)


if __name__ == "__main__":
    test_narrative_values_match_table()
    test_2020_layout_is_rejected_not_guessed()
    test_closed_fish_markets_are_flagged()
    print(f"OK: all {len(CASES)} narrative spot checks match; 2020 layout rejected; closures flagged")
