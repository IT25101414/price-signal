#!/usr/bin/env python3
"""
Extract the price table from CBSL Daily Price Report PDFs into a tidy CSV.

    pip install pdfplumber
    python extract_prices.py data/raw prices.csv

Why position-based: the PDF text layer drops empty (grey) cells and splits numbers
into fragments, so splitting a line on spaces assigns prices to the wrong market.
We bin every token by its x-position instead, and we read each section's market
names from the PDF's own header rows (also by x-position) rather than hard-coding them.

Parser version "table-layout-v3" was developed on reports from Nov 2020 to
October 2026 (2-page, 5-column layout). Reports in other layouts (for example June
2020: 4 pages, 6 price columns, no Unit column) are REJECTED with a clear message
and are never guessed at.

Changes in v3:
  * the section header row (V E G E T A B L E S) is no longer cut off when it sits
    directly under the "Today" header row (Nov 2020 reports)
  * a report with no extracted rows is a FAILURE, not a silent success
  * comparison header accepts "Friday" / "last Friday" / "Last Friday" and derives the
    weekday from the date when only the date is printed
  * the full failure and warning lists are written to failed_files.txt / warnings.txt

Output: one row per (report, item, market):
  report_date, section, item, unit, price_type, market, market_assumed,
  price_prior, price_prior_status, price_today, price_today_status,
  prior_label, prior_date, narrative_basis, report_notes, source_file, parser_version
price_*_status is "ok" or "n.a." (CBSL reported no price). A grey/empty cell in the PDF
is "not applicable" and produces no row.
market_assumed is True when a section prints its own market header row but leaves this
column unnamed, so the name is inherited from the table's top header.
narrative_basis is whether the page-1 summary quotes "retail" or "wholesale" prices
(it was wholesale in 2021 reports).
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

PARSER_VERSION = "table-layout-v3"
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
WEEKDAYS = "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
MARKET_NAMES = {"Pettah", "Dambulla", "Narahenpita", "Peliyagoda", "Negombo", "Marandagahamula"}
# Five price columns: first two are wholesale, last three retail (checked against the
# narrative text of each report in test_extract_prices.py).
PRICE_TYPES = ["wholesale", "wholesale", "retail", "retail", "retail"]

FIELDS = ["report_date", "section", "item", "unit", "price_type", "market", "market_assumed",
          "price_prior", "price_prior_status", "price_today", "price_today_status",
          "prior_label", "prior_date", "narrative_basis", "report_notes",
          "source_file", "parser_version"]


class UnsupportedLayout(ValueError):
    """The PDF is not in a layout this parser was built for."""


def parse_cell(text):
    t = text.replace(",", "").strip()
    t = re.sub(r"\([a-zA-Z]\)$", "", t)          # footnote marker, e.g. "150.00(a)"
    if not t:
        return None, ""
    if t.lower().startswith("n.a"):
        return None, "n.a."
    if re.fullmatch(r"\d+(\.\d+)?", t):
        return float(t), "ok"
    raise ValueError(f"unparseable cell {text!r}")


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


def clean_name(text):
    return text.strip().rstrip("*:").strip()


def parse_pdf(path):
    """Return (rows, warnings) for one PDF. Raises UnsupportedLayout / ValueError."""
    path = Path(path)
    warnings = []
    with pdfplumber.open(path) as pdf:
        alltext = "\n".join((p.extract_text() or "") for p in pdf.pages)
        tpages = [p for p in pdf.pages if "Wholesale and Retail Prices" in (p.extract_text() or "")]
        if not tpages:
            raise UnsupportedLayout("no page contains the price table")
        if len(tpages) > 1 or len(pdf.pages) > 2:
            raise UnsupportedLayout(f"{len(pdf.pages)} pages / {len(tpages)} table pages "
                                    "(expected a 2-page report with one table page)")
        page = tpages[0]
        text = page.extract_text() or ""
        words = page.extract_words()

    m = re.search(r"(\d{1,2})\s+(%s),?\s+(\d{4})" % "|".join(MONTHS), text)
    if not m:
        raise ValueError("report date not found on table page")
    report_date = date(int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)))
    fm = re.search(r"price_report_(\d{8})", path.name)
    if fm and datetime.strptime(fm.group(1), "%Y%m%d").date() != report_date:
        warnings.append(f"{path.name}: date in file name differs from date in report ({report_date})")

    # The header ends where the first section row ("V E G E T A B L E S") begins. A fixed
    # cut-off does not work: the "Today" row sits at y=57 to 107 depending on the report.
    letter_rows = {}
    for w in words:
        if len(w["text"]) == 1 and w["text"].isalpha() and w["x0"] > 150:
            letter_rows.setdefault(round(w["top"]), []).append(w)
    sec_tops = [t for t, ws in letter_rows.items() if len(ws) >= 3]
    header_limit = (min(sec_tops) - 1) if sec_tops else 100
    header = [w for w in words if w["top"] < header_limit]
    today_c = sorted((w["x0"] + w["x1"]) / 2 for w in header if w["text"] == "Today")
    unit_hdr = [w for w in header if w["text"] == "Unit"]
    if len(today_c) != 5 or not unit_hdr:
        raise UnsupportedLayout(f"header has {len(today_c)} 'Today' columns and "
                                f"{'a' if unit_hdr else 'no'} 'Unit' column (expected 5 and a Unit column)")
    header_bottom = max(w["bottom"] for w in header if w["text"] == "Today")

    # Comparison basis: "Yesterday" normally; otherwise a weekday and a date, printed as
    # "Last Friday dd.mm.yyyy", "last Friday dd.mm.yyyy" or just "Friday dd.mm.yyyy".
    htxt = " ".join(w["text"] for w in header if w["x0"] > 150 and w["top"] > 60)
    lm = re.search(r"(?:last\s+)?(%s)" % WEEKDAYS, htxt, re.I)
    dm = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", htxt)
    if dm:
        prior_date = date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)))
        prior_label = (f"Last {lm.group(1).capitalize()}" if lm
                       else f"Last {prior_date.strftime('%A')}")
    elif lm:
        raise ValueError(f"ambiguous comparison header: {htxt!r}")
    else:
        prior_label, prior_date = "Yesterday", None

    bm = re.search(r"denote the\s+(retail|wholesale)\s+prices", alltext, re.I)
    narrative_basis = bm.group(1).lower() if bm else ""
    notes = [ln.strip(" *") for ln in text.splitlines()
             if re.search(r"not in operation|not available|were not|was not", ln, re.I)]
    report_notes = " | ".join(n for n in notes if n)

    # Some reports (Jan-Feb 2021) are drawn ~1.55x larger than the usual ones, so the fixed
    # offsets below are scaled by the real column spacing. Normal-size pages stay at 1.0.
    scale = ((today_c[-1] - today_c[0]) / 4) / 92.3
    if 0.9 <= scale <= 1.1:
        scale = 1.0
    label_max = unit_hdr[0]["x0"] - 10 * scale
    num_start = today_c[0] - 60 * scale
    split = [t - 21 * scale for t in today_c]         # prior | today boundary inside each pair
    pair_edges = [(today_c[i] + today_c[i + 1] - 42 * scale) / 2 for i in range(4)]

    def pair_of(c):
        return sum(c > e for e in pair_edges)

    # Top header: market name for each of the 5 columns.
    top_names = {}
    for w in header:
        if w["x0"] > 150 and clean_name(w["text"]) in MARKET_NAMES:
            top_names.setdefault(pair_of((w["x0"] + w["x1"]) / 2), clean_name(w["text"]))
    if sorted(top_names) != [0, 1, 2, 3, 4]:
        raise UnsupportedLayout(f"top header names markets for columns {sorted(top_names)} only")
    top_list = [top_names[i] for i in range(5)]

    out = []
    section, sub, has_data = None, None, False
    # Nov 2020 reports put the section header row directly under the "Today" row, so keep
    # everything below the header (not 2pt further down). Rows without a unit are skipped.
    body = [w for w in words if w["top"] > header_bottom]
    for row in group_rows(body):
        letters = [w["text"] for w in row if w["x0"] > 150]
        if letters and all(len(t) == 1 and t.isalpha() for t in letters) and len(letters) >= 3:
            section, sub, has_data = "".join(letters).upper(), {}, False
            continue
        label = " ".join(w["text"] for w in row if w["x0"] < label_max)
        unit = " ".join(w["text"] for w in row if label_max <= w["x0"] < num_start)
        if not (label and unit.startswith("Rs.")):
            if section is not None and not has_data:          # section sub-header row
                for w in row:
                    if w["x0"] > 150 and clean_name(w["text"]) in MARKET_NAMES:
                        sub.setdefault(pair_of((w["x0"] + w["x1"]) / 2), clean_name(w["text"]))
            continue
        if section is None:
            warnings.append(f"{path.name}: row {label!r} found before any section header")
            continue
        has_data = True
        cells = {}
        for w in row:
            c = (w["x0"] + w["x1"]) / 2
            if w["x0"] < num_start:
                continue
            i = pair_of(c)
            side = "prior" if c < split[i] else "today"
            cells.setdefault((i, side), []).append((w["x0"], w["text"]))
        seen = set()
        for i in range(5):
            raw = {s: "".join(t for _, t in sorted(cells.get((i, s), []))) for s in ("prior", "today")}
            if not raw["prior"] and not raw["today"]:
                continue                                  # grey cell: not applicable
            if sub:                                       # section prints its own header row
                market, assumed = (sub[i], False) if i in sub else (top_list[i], True)
            else:
                market, assumed = top_list[i], False
            ptype = PRICE_TYPES[i]
            if (ptype, market) in seen:
                warnings.append(f"{path.name}: {label!r} has two columns named {ptype} {market}; "
                                "second one skipped")
                continue
            seen.add((ptype, market))
            try:
                pv, ps = parse_cell(raw["prior"])
                tv, ts = parse_cell(raw["today"])
            except ValueError as e:
                warnings.append(f"{path.name}: {label!r} column {i + 1}: {e}")
                continue
            out.append(dict(report_date=report_date.isoformat(), section=section, item=label,
                            unit=unit, price_type=ptype, market=market, market_assumed=assumed,
                            price_prior=pv, price_prior_status=ps, price_today=tv,
                            price_today_status=ts, prior_label=prior_label,
                            prior_date=prior_date.isoformat() if prior_date else "",
                            narrative_basis=narrative_basis, report_notes=report_notes,
                            source_file=path.name, parser_version=PARSER_VERSION))
    if not out:
        raise ValueError("no price rows extracted")
    return out, warnings


def check_consistency(rows):
    """Each report states the previous price, so today's price in report D must equal the
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
    seen_dates = {}                                  # report_date -> first file that gave it
    for p in pdfs:
        try:
            r, w = parse_pdf(p)
            rd = r[0]["report_date"]
            if rd in seen_dates:                     # same report published under two names
                failed.append((p.name, f"DuplicateReport: report date {rd} already read "
                                       f"from {seen_dates[rd]}; this copy skipped"))
                continue
            seen_dates[rd] = p.name
            rows += r
            all_warn += w
        except Exception as e:                       # quarantine, never guess
            failed.append((p.name, f"{type(e).__name__}: {e}"))
    with open(dest, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(rows)
    print(f"{len(pdfs)} PDFs, {len(rows)} price rows written to {dest}")
    print(f"{len(failed)} files failed to parse, {len(all_warn)} warnings")
    failed_names = {n for n, _ in failed}
    by_year = {}
    for p in pdfs:
        y = p.name[:4]
        ok_n, bad_n = by_year.get(y, (0, 0))
        by_year[y] = (ok_n, bad_n + 1) if p.name in failed_names else (ok_n + 1, bad_n)
    print("  year: parsed / failed")
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y][0]} / {by_year[y][1]}")
    if failed:
        latest = max(failed)
        print(f"  most recent failure: {latest[0]} - {latest[1]}")
    # full lists, so nothing is hidden by the short on-screen preview
    with open("failed_files.txt", "w", encoding="utf-8") as fh:
        for n, e in failed:
            fh.write(f"{n}\t{e}\n")
    with open("warnings.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(all_warn))
    for n, e in failed[:5]:
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
