#!/usr/bin/env python3
"""
Write data/recent_prices.csv: the last ~375 calendar days of the four price series the website shows
(Dambulla wholesale and the three Colombo series), for the items on today's cards.

    python3 export_recent.py prices_all.csv           # needs cards.csv (run model.py first)

Why: prices_all.csv is large and git-ignored, so a fresh clone would show no price charts. This small slice is
committed instead. The prices are the Central Bank of Sri Lanka's, published by its Statistics Department; its
reply of 12 Oct 2026 (docs/cbsl_reply_2026-10-12.pdf) says the data are public and asks for attribution.
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "web"))
import build_db  # noqa: E402


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    cards = build_db.load_cards(ROOT / "cards.csv")
    items = {r["item"] for r in cards}
    df = build_db.recent_frame(argv[0], items)
    out = ROOT / "data" / "recent_prices.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["report_date", "item", "series", "price_rs"])
        for d, i, s, p in zip(df["report_date"], df["item"], df["series"], df["price_rs"]):
            w.writerow([d.date().isoformat(), i, s, f"{p:g}"])
    print(f"wrote {out}: {len(df)} rows, {df['report_date'].min().date()} to {df['report_date'].max().date()}")


if __name__ == "__main__":
    main(sys.argv[1:])
