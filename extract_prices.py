#!/usr/bin/env python3
"""
Extract the price table from CBSL Daily Price Report PDFs into a tidy CSV.

    pip install pdfplumber
    python extract_prices.py data/raw prices.csv

Why position-based: the PDF text layer drops empty (grey) cells and splits numbers
into fragments, so splitting a line on spaces assigns prices to the wrong market.
We bin every token by its x-position instead.

Parser version "2026-layout-v1" was developed and verified on reports dated
2-9 October 2026 ONLY. Older reports may use different layouts: the script flags
anything it cannot parse and never guesses silently.

Output columns: one row per (report, item, market):
  report_date, section, item, unit, price_type, market, market_assumed,
  price_prior, price_prior_status, price_today, price_today_status,
  prior_label, prior_date, source_file, parser_version
price_*_status is "ok" or "n.a." (reported as not available by CBSL). A cell that is
grey/empty in the PDF is "not applicable" and produces no row.
"""
import csv
import logging
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pdfplumber

# pdfminer logs harmless colour-operator warnings for some PDFs; keep real output readable
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.ERROR)

PARSER_VERSION = "2026-layout-v1"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Five price columns (pairs of prior/today) per row. Market names change by section.
# 3rd element = True when the header is blank in the PDF and we infer the name.
_DEFAULT = [("wholesale", "Pettah", False), ("wholesale", "Dambulla", False),
            ("retail", "Pettah", False), ("retail", "Dambulla", False),
            ("retail", "Narahenpita", False)]
_RICE = [("wholesale", "Pettah", True), ("wholesale", "Marandagahamula", False),
         ("retail", "Pettah", False), ("retail", "Dambulla", False),
         ("retail", "Narahenpita", False)]
_FISH = [("wholesale", "Peliyagoda", False), ("wholesale", "Negombo", False),
         None, ("retail", "Negombo", False), ("retail", "Narahenpita", True)]
SECTION_MARKETS = {"RICE": _RICE, "FISH": _FISH}

FIELDS = ["report_date", "section", "item", "unit", "price_type", "market", "market_assumed",
          "price_prior", "price_prior_status", "price_today", "price_today_status",
          "prior_label", "prior_date", "source_file", "parser_version"]


def parse_cell(text):
    t = text.replace(",", "").strip()
    if not t:
        return None, ""
    if t.lower().startswith("n.a"):
        return None, "n.a."
    if re.fullmatch(r"\d+(\.\d+)?", t):
        return float(t), "ok"
    raise ValueError(f"unparseable cell {text!r}")


def find_table_page(pdf):
    for p in pdf.pages:
        if "Wholesale and Retail Prices" in (p.extract_text() or ""):
            return p
    raise ValueError("no page contains the price table")


def group_rows(words, tol=2.5):
    rows, cur, cur_top = [], [], None
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if cur_top is None or abs(w["top"] - cur_top) <= tol:
            cur.append(w)
            cur_top = w["top"] if cur_top is None else cur_top
        else:
            rows.append(cur)
            cur, cur_top = [w], w["top"]
    if cur:
        rows.append(cur)
    return rows


def parse_pdf(path):
    """Return (rows, warnings) for one PDF."""
    path = Path(path)
    warnings = []
    with pdfplumber.open(path) as pdf:
        page = find_table_page(pdf)
        text = page.extract_text() or ""
        words = page.extract_words()

    m = re.search(r"(\d{1,2})\s+(%s)\s+(\d{4})" % "|".join(MONTHS), text)
    if not m:
        raise ValueError("report date not found on table page")
    report_date = date(int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)))
    fm = re.search(r"price_report_(\d{8})", path.name)
    if fm and datetime.strptime(fm.group(1), "%Y%m%d").date() != report_date:
        warnings.append(f"{path.name}: date in file name differs from date in report ({report_date})")

    header = [w for w in words if w["top"] < 100]
    today_c = sorted((w["x0"] + w["x1"]) / 2 for w in header if w["text"] == "Today")
    unit_hdr = [w for w in header if w["text"] == "Unit"]
    if len(today_c) != 5 or not unit_hdr:
        raise ValueError(f"unexpected header layout (found {len(today_c)} 'Today' columns)")
    header_bottom = max(w["bottom"] for w in header if w["text"] == "Today")

    # Comparison basis: "Yesterday" normally, "Last Friday dd.mm.yyyy" on Mondays.
    htxt = " ".join(w["text"] for w in header if w["x0"] > 150 and w["top"] > 60)
    lm = re.search(r"Last\s+([A-Za-z]+)", htxt)
    dm = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", htxt)
    if lm and dm:
        prior_label = f"Last {lm.group(1)}"
        prior_date = date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)))
    elif lm or dm:
        raise ValueError(f"ambiguous comparison header: {htxt!r}")
    else:
        prior_label, prior_date = "Yesterday", None

    label_max = unit_hdr[0]["x0"] - 10
    num_start = today_c[0] - 60
    split = [t - 21 for t in today_c]                 # prior | today boundary inside each pair
    pair_edges = [(today_c[i] + today_c[i + 1] - 42) / 2 for i in range(4)]

    def pair_of(c):
        return sum(c > e for e in pair_edges)

    out, section = [], None
    body = [w for w in words if w["top"] > header_bottom + 2]
    for row in group_rows(body):
        letters = [w["text"] for w in row if w["x0"] > 150]
        if letters and all(len(t) == 1 and t.isalpha() for t in letters) and len(letters) >= 3:
            section = "".join(letters).upper()
            continue
        label = " ".join(w["text"] for w in row if w["x0"] < label_max)
        unit = " ".join(w["text"] for w in row if label_max <= w["x0"] < num_start)
        if not label or not unit.startswith("Rs."):
            continue
        if section is None:
            warnings.append(f"{path.name}: row {label!r} found before any section header")
            continue
        cells = {}
        for w in row:
            c = (w["x0"] + w["x1"]) / 2
            if w["x0"] < num_start:
                continue
            i = pair_of(c)
            side = "prior" if c < split[i] else "today"
            cells.setdefault((i, side), []).append((w["x0"], w["text"]))
        mapping = SECTION_MARKETS.get(section, _DEFAULT)
        for i in range(5):
            raw = {s: "".join(t for _, t in sorted(cells.get((i, s), []))) for s in ("prior", "today")}
            if not raw["prior"] and not raw["today"]:
                continue                                  # grey cell: not applicable
            if mapping[i] is None:
                warnings.append(f"{path.name}: {label!r} has data in an unexpected column {i + 1}")
                continue
            try:
                pv, ps = parse_cell(raw["prior"])
                tv, ts = parse_cell(raw["today"])
            except ValueError as e:
                warnings.append(f"{path.name}: {label!r} column {i + 1}: {e}")
                continue
            ptype, market, assumed = mapping[i]
            out.append(dict(report_date=report_date.isoformat(), section=section, item=label,
                            unit=unit, price_type=ptype, market=market, market_assumed=assumed,
                            price_prior=pv, price_prior_status=ps, price_today=tv,
                            price_today_status=ts, prior_label=prior_label,
                            prior_date=prior_date.isoformat() if prior_date else "",
                            source_file=path.name, parser_version=PARSER_VERSION))
    if not out:
        warnings.append(f"{path.name}: no price rows extracted")
    return out, warnings


def check_consistency(rows):
    """Each report states yesterday's price, so today's price in report D must equal the
    'prior' price in the next report. Returns (n_compared, mismatches, n_no_reference)."""
    by_date = {}
    for r in rows:
        key = (r["section"], r["item"], r["price_type"], r["market"])
        by_date.setdefault(r["report_date"], {})[key] = r
    compared, bad, noref = 0, [], 0
    for d, recs in by_date.items():
        later = datetime.fromisoformat(d).date()
        for key, r in recs.items():
            ref = r["prior_date"] or (later - timedelta(days=1)).isoformat()
            ref_rec = by_date.get(ref, {}).get(key)
            if ref_rec is None:
                noref += 1
                continue
            a, b = ref_rec["price_today"], r["price_prior"]
            if a is None and b is None:
                continue
            compared += 1
            if a != b:
                bad.append((ref, d, key, a, b))
    return compared, bad, noref


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    src, dest = Path(argv[1]), Path(argv[2])
    pdfs = sorted(src.glob("*.pdf")) if src.is_dir() else [src]
    rows, all_warn, failed = [], [], []
    for p in pdfs:
        try:
            r, w = parse_pdf(p)
            rows += r
            all_warn += w
        except Exception as e:                       # quarantine, never guess
            failed.append((p.name, str(e)))
    with open(dest, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(rows)
    print(f"{len(pdfs)} PDFs, {len(rows)} price rows written to {dest}")
    print(f"{len(failed)} files failed to parse, {len(all_warn)} warnings")
    for n, e in failed:
        print("  FAILED", n, "-", e)
    for w in all_warn[:20]:
        print("  WARN", w)
    comp, bad, noref = check_consistency(rows)
    print(f"consistency: {comp} prior/today pairs compared across reports, "
          f"{len(bad)} mismatches, {noref} rows without a reference report")
    for ref, d, key, a, b in bad[:20]:
        print(f"  MISMATCH {key}: {ref} today={a} vs {d} prior={b}")


if __name__ == "__main__":
    main(sys.argv)
