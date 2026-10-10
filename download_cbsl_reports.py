#!/usr/bin/env python3
"""
Download CBSL Daily Price Report PDFs politely and keep a manifest.

Usage (test first!):
    pip install requests beautifulsoup4
    python download_cbsl_reports.py --limit 10
    python download_cbsl_reports.py            # full run, resumes automatically

NOT TESTED against the live site (the author's environment could not reach it).
Run with --limit 10 first and inspect data/manifest.csv and data/raw/.

Before running: read https://www.cbsl.gov.lk/robots.txt and the site terms, and
send your permission request. The script refuses to fetch URLs robots.txt disallows.
"""
import argparse
import csv
import hashlib
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE = "https://www.cbsl.gov.lk"
# Listing used in the browser; the real Daily Price Report index page is better
# if it has one. Pass it with --index-url.
DEFAULT_INDEX = BASE + "/en/statistics/economic-indicators/price-report"
USER_AGENT = "ModelX2-student-project (contact: it25101414@my.sliit.lk)"
DELAY_SECONDS = 10  # robots.txt says Crawl-delay: 10 -- do not lower this
DATA = Path("data")
RAW = DATA / "raw"
MANIFEST = DATA / "manifest.csv"
FIELDS = ["title", "page_url", "pdf_url", "report_date", "file", "sha256", "status", "fetched_at"]

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def parse_date(text):
    """Try several title formats. Returns ISO date string or ''. Always verify later."""
    t = text.replace(",", " ")
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", t)  # 01.06.2017
    if m:
        d, mo, y = map(int, m.groups())
    else:
        m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", t)  # 22 February 2017
        if not m or m.group(2).lower() not in MONTHS:
            return ""
        d, mo, y = int(m.group(1)), MONTHS[m.group(2).lower()], int(m.group(3))
    try:
        return datetime(y, mo, d).date().isoformat()
    except ValueError:
        return ""


class Fetcher:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.rp = RobotFileParser()
        self.rp.set_url(BASE + "/robots.txt")
        try:
            self.rp.read()
        except Exception as e:  # if robots.txt cannot be read, stop and ask the user
            raise SystemExit(f"Could not read robots.txt ({e}). Check it manually before scraping.")

    def get(self, url, retries=3):
        if not self.rp.can_fetch(USER_AGENT, url):
            raise PermissionError(f"robots.txt disallows {url}")
        for attempt in range(retries):
            try:
                time.sleep(DELAY_SECONDS)
                r = self.s.get(url, timeout=60)
                if r.status_code == 200:
                    return r
                if r.status_code in (403, 404):
                    return r
            except requests.RequestException:
                pass
            time.sleep(5 * (attempt + 1))
        return None


def collect_report_links(f, index_url, max_pages, start_page=0):
    """Walk ?page=N on the listing and collect links whose text mentions 'daily price report'."""
    found = {}
    for page in range(start_page, start_page + max_pages):
        url = index_url if page == 0 else f"{index_url}?page={page}"
        r = f.get(url)
        if r is None or r.status_code != 200:
            print(f"stopping at page {page}: no usable response")
            break
        soup = BeautifulSoup(r.text, "html.parser")
        new = 0
        for a in soup.find_all("a", href=True):
            title = " ".join(a.get_text().split())
            if re.search(r"daily price report", title, re.I):
                link = urljoin(BASE, a["href"])
                # Skip the menu/breadcrumb link back to the index page: a real report
                # link either points at a PDF or has a date in its title.
                is_pdf = urlparse(link).path.lower().endswith(".pdf")
                if not (is_pdf or parse_date(title)):
                    continue
                if link not in found:
                    found[link] = title
                    new += 1
        print(f"page {page}: {new} new report links (total {len(found)})")
        if new == 0:
            break
    return found


def load_done():
    if not MANIFEST.exists():
        return set()
    with open(MANIFEST, newline="", encoding="utf-8") as fh:
        return {row["page_url"] for row in csv.DictReader(fh) if row["status"] == "ok"}


def append_row(row):
    new_file = not MANIFEST.exists()
    with open(MANIFEST, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)


def process(f, page_url, title):
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row = dict(title=title, page_url=page_url, pdf_url="", report_date=parse_date(title),
               file="", sha256="", status="", fetched_at=now)
    if page_url.lower().endswith(".pdf"):
        pdf_url = page_url
    else:
        r = f.get(page_url)
        if r is None or r.status_code != 200:
            row["status"] = "page_failed"
            return row
        soup = BeautifulSoup(r.text, "html.parser")
        pdfs = [urljoin(BASE, a["href"]) for a in soup.find_all("a", href=True)
                if urlparse(a["href"]).path.lower().endswith(".pdf")]
        if not pdfs:
            row["status"] = "no_pdf_link"
            return row
        pdf_url = pdfs[0]
        if len(pdfs) > 1:
            row["status"] = "multiple_pdfs_check_manually"
    row["pdf_url"] = pdf_url
    r = f.get(pdf_url)
    if r is None or r.status_code != 200 or not r.content.startswith(b"%PDF"):
        row["status"] = "pdf_failed"
        return row
    name = (row["report_date"] or re.sub(r"\W+", "_", title)[:60]) + "__" + Path(urlparse(pdf_url).path).name
    path = RAW / name
    path.write_bytes(r.content)  # raw files are never modified afterwards
    row["file"] = str(path)
    row["sha256"] = hashlib.sha256(r.content).hexdigest()
    if not row["status"]:
        row["status"] = "ok"
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index-url", default=DEFAULT_INDEX)
    ap.add_argument("--max-pages", type=int, default=300, help="how many listing pages to read (12 reports each)")
    ap.add_argument("--start-page", type=int, default=0, help="first listing page (0 = newest); use e.g. 100 to sample older years")
    ap.add_argument("--limit", type=int, default=0, help="stop after N reports (use 10 to test)")
    args = ap.parse_args()

    if "YOUR_EMAIL" in USER_AGENT:
        raise SystemExit("Edit USER_AGENT in the script and put your real contact email first.")
    RAW.mkdir(parents=True, exist_ok=True)
    f = Fetcher()
    try:
        links = collect_report_links(f, args.index_url, args.max_pages, args.start_page)
    except PermissionError as e:
        raise SystemExit(f"{e}\nUse the Daily Price Report page from the Statistics menu with --index-url instead.")
    done = load_done()
    todo = [(u, t) for u, t in links.items() if u not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(links)} reports found, {len(done)} already downloaded, {len(todo)} to fetch")
    for i, (u, t) in enumerate(todo, 1):
        row = process(f, u, t)
        append_row(row)
        print(f"[{i}/{len(todo)}] {row['status'] or 'ok'}  {t}")


if __name__ == "__main__":
    main()
