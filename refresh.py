#!/usr/bin/env python3
"""
Daily refresh: fetch the newest Central Bank report(s), parse them, append them to the
price table, and log what happened.

    python3 refresh.py                      # uses prices_all.csv
    python3 refresh.py --prices prices_all.csv

It reuses download_cbsl_reports.py (polite fetching, robots.txt, 10 s delay, manifest) and
extract_prices.py (position-based parser), so nothing here re-implements them.

What one run does
  1. Reads ONLY the first listing page (the newest 12 reports): about 1 request.
  2. For every listed report whose date is not yet in the price table: downloads it (or
     re-uses the file already in data/raw) and parses it. A report that cannot be parsed is
     logged and left out. It is never guessed.
  3. Appends new rows to the price table (a date already in the table is never added twice).
  4. Writes one line to data/refresh_log.csv: when it ran, the newest date listed on the
     site, the newest date in the table, how many reports were new / downloaded / parsed,
     any failures, and a status.

Statuses:  ok | no_new_report | behind | partial | failed | source_unavailable
  behind = nothing new this run, but the site lists a newer report than the table holds
           (an earlier report could not be read). guard.py turns this into a refusal.

Exit code: 0 for ok / no_new_report, 1 for behind / partial / failed, 2 for source_unavailable.
"""
import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import download_cbsl_reports as dl
import extract_prices as ex

LOG_FIELDS = ["run_at_utc", "newest_listed", "latest_in_table", "new_links", "downloaded_ok",
              "parsed_ok", "failures", "status", "message"]


def log_path():
    return dl.DATA / "refresh_log.csv"


def read_table_dates(prices_csv):
    p = Path(prices_csv)
    if not p.exists():
        return set()
    with open(p, newline="", encoding="utf-8") as fh:
        return {row["report_date"] for row in csv.DictReader(fh)}


def append_rows(prices_csv, rows):
    p = Path(prices_csv)
    new_file = not p.exists() or p.stat().st_size == 0
    with open(p, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=ex.FIELDS)
        if new_file:
            w.writeheader()
        w.writerows(rows)


def manifest_files():
    """page_url -> local file, for reports already downloaded successfully."""
    if not dl.MANIFEST.exists():
        return {}
    with open(dl.MANIFEST, newline="", encoding="utf-8") as fh:
        return {r["page_url"]: r["file"] for r in csv.DictReader(fh) if r["status"] == "ok" and r["file"]}


def write_log(result):
    lp = log_path()
    lp.parent.mkdir(parents=True, exist_ok=True)
    new_file = not lp.exists()
    with open(lp, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(result)


def last_log_row():
    lp = log_path()
    if not lp.exists():
        return None
    with open(lp, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows[-1] if rows else None


def run(prices_csv="prices_all.csv", index_url=None, fetcher=None):
    index_url = index_url or dl.DEFAULT_INDEX
    res = dict(run_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), newest_listed="",
               latest_in_table="", new_links=0, downloaded_ok=0, parsed_ok=0, failures="",
               status="", message="")
    dl.RAW.mkdir(parents=True, exist_ok=True)
    known = read_table_dates(prices_csv)
    res["latest_in_table"] = max(known) if known else ""
    try:
        f = fetcher or dl.Fetcher()
        links = dl.collect_report_links(f, index_url, 1, 0)       # newest 12 reports only
    except (SystemExit, Exception) as e:                          # robots.txt unreadable, network down...
        res.update(status="source_unavailable", message=f"{type(e).__name__}: {e}")
        write_log(res)
        return res
    if not links:
        res.update(status="source_unavailable", message="the listing page returned no usable report links")
        write_log(res)
        return res

    dated = [(dl.parse_date(t), u, t) for u, t in links.items()]
    res["newest_listed"] = max((d for d, _, _ in dated if d), default="")
    files = manifest_files()
    failures = []
    for d, url, title in sorted(dated, key=lambda x: x[0] or ""):          # oldest first
        if d and d in known:
            continue
        res["new_links"] += 1
        if url in files and Path(files[url]).exists():                     # downloaded before, never parsed
            path = files[url]
            res["downloaded_ok"] += 1
        else:
            row = dl.process(f, url, title)
            dl.append_row(row)
            if row["status"] != "ok":
                failures.append(f"{title}: download {row['status'] or 'failed'}")
                continue
            res["downloaded_ok"] += 1
            path = row["file"]
        try:
            rows, warnings = ex.parse_pdf(path)
            if warnings:
                raise ValueError("parser warnings: " + " | ".join(warnings))
            rd = rows[0]["report_date"]
            if rd in known:
                failures.append(f"{title}: report date {rd} is already in the table; not added twice")
                continue
            append_rows(prices_csv, rows)
            known.add(rd)
            res["parsed_ok"] += 1
        except Exception as e:                                             # quarantine, never guess
            failures.append(f"{title}: {type(e).__name__}: {e}")
    res["failures"] = " | ".join(failures)
    res["latest_in_table"] = max(known) if known else ""
    behind = bool(res["newest_listed"]) and res["latest_in_table"] < res["newest_listed"]
    if res["new_links"] == 0:
        res["status"] = "behind" if behind else "no_new_report"
        res["message"] = ("the site lists a newer report than the table holds" if behind
                          else "table is up to date with the site")
    elif failures and res["parsed_ok"] == 0:
        res["status"] = "failed"
        res["message"] = "no new report could be added"
    elif failures:
        res["status"] = "partial"
        res["message"] = f"{res['parsed_ok']} added, {len(failures)} could not be added"
    else:
        res["status"] = "ok"
        res["message"] = f"{res['parsed_ok']} new report(s) added"
    write_log(res)
    return res


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prices", default="prices_all.csv")
    args = ap.parse_args(argv)
    r = run(args.prices)
    print(f"refresh: {r['status']}. {r['message']}. newest listed {r['newest_listed'] or '-'}, "
          f"latest in table {r['latest_in_table'] or '-'}; new {r['new_links']}, "
          f"parsed {r['parsed_ok']}.")
    if r["failures"]:
        print("  failures:", r["failures"])
    return {"ok": 0, "no_new_report": 0, "source_unavailable": 2}.get(r["status"], 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
