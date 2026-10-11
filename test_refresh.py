"""
Tests for refresh.py using a fake website (no network). Needs a few sample PDFs:
    SAMPLES_DIR=path/to/pdfs pytest test_refresh.py
It looks for the reports dated 8 and 9 October 2026.
"""
import csv
import os
from datetime import date
from pathlib import Path

import pytest

import guard
import refresh

SAMPLES = Path(os.environ.get("SAMPLES_DIR", "samples")).resolve()   # absolute: the tests change directory
P8 = next(iter(SAMPLES.glob("*2026-10-08__*.pdf")), None) or next(iter(SAMPLES.glob("2026-10-08__*.pdf")), None)
P9 = next(iter(SAMPLES.glob("2026-10-09__*.pdf")), None)
pytestmark = pytest.mark.skipif(not (P8 and P9), reason="sample PDFs for 8 and 9 Oct 2026 not found")

IDX = refresh.dl.DEFAULT_INDEX
BASE = "https://www.cbsl.gov.lk/sites/default/files/x/"


class Resp:
    def __init__(self, status=200, text="", content=b""):
        self.status_code, self.text, self.content = status, text, content


class FakeFetcher:
    def __init__(self, listing, files):
        self.listing, self.files = listing, dict(files)
        self.requests = []

    def get(self, url, retries=3):
        self.requests.append(url)
        if url == IDX:
            return Resp(200, self.listing) if self.listing is not None else Resp(503)
        if url in self.files:
            return Resp(200, "", self.files[url])
        return Resp(404)


def listing(entries):
    links = "".join(f'<a href="{u}">{t}</a>' for u, t in entries)
    return f'<html><a href="https://www.cbsl.gov.lk/en/menu">Daily Price Report</a>{links}</html>'


U8, U9, U12 = BASE + "a8.pdf", BASE + "a9.pdf", BASE + "a12.pdf"
T8, T9, T12 = ("Daily Price Report - 08 October 2026", "Daily Price Report - 09 October 2026",
               "Daily Price Report - 12 October 2026")


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    files = {U8: P8.read_bytes(), U9: P9.read_bytes()}
    return files


def test_first_run_reads_and_appends_both_reports(env):
    f = FakeFetcher(listing([(U9, T9), (U8, T8)]), env)
    r = refresh.run("prices_test.csv", fetcher=f)
    assert r["status"] == "ok" and r["new_links"] == 2 and r["parsed_ok"] == 2
    assert refresh.read_table_dates("prices_test.csv") == {"2026-10-08", "2026-10-09"}
    assert r["newest_listed"] == "2026-10-09" == r["latest_in_table"]
    assert refresh.last_log_row()["status"] == "ok"


def test_second_run_adds_nothing_and_downloads_nothing(env):
    f = FakeFetcher(listing([(U9, T9), (U8, T8)]), env)
    refresh.run("prices_test.csv", fetcher=f)
    f2 = FakeFetcher(listing([(U9, T9), (U8, T8)]), env)
    r = refresh.run("prices_test.csv", fetcher=f2)
    assert r["status"] == "no_new_report" and r["new_links"] == 0
    assert f2.requests == [IDX]                                   # only the listing page was requested
    n_rows = sum(1 for _ in open("prices_test.csv")) - 1
    assert n_rows == sum(1 for _ in open("prices_test.csv")) - 1 and n_rows > 300


def test_unreadable_new_report_is_logged_not_guessed_and_guard_refuses(env):
    files = dict(env)
    files[U12] = b"%PDF-1.4 this is not a real report"
    f = FakeFetcher(listing([(U12, T12), (U9, T9), (U8, T8)]), files)
    r = refresh.run("prices_test.csv", fetcher=f)
    assert r["status"] == "partial" and r["parsed_ok"] == 2
    assert "12 October 2026" in r["failures"]
    assert refresh.read_table_dates("prices_test.csv") == {"2026-10-08", "2026-10-09"}
    assert r["newest_listed"] == "2026-10-12" and r["latest_in_table"] == "2026-10-09"
    # the guard turns "site is ahead of the table" into a refusal
    prices = guard.load_prices("prices_test.csv")
    v = guard.assess(prices, "Lime", today=date(2026, 10, 12), newest_listed=date(2026, 10, 12), min_obs=1)
    assert v.status == "report_not_read"
    # a second run retries the parse from the saved file, without downloading again
    n_manifest = sum(1 for _ in open("data/manifest.csv"))
    f2 = FakeFetcher(listing([(U12, T12), (U9, T9), (U8, T8)]), files)
    r2 = refresh.run("prices_test.csv", fetcher=f2)
    assert r2["status"] == "failed" and f2.requests == [IDX]
    assert sum(1 for _ in open("data/manifest.csv")) == n_manifest


def test_site_down_is_reported_as_source_unavailable(env):
    r = refresh.run("prices_test.csv", fetcher=FakeFetcher(None, env))
    assert r["status"] == "source_unavailable"
    assert not Path("prices_test.csv").exists()


def test_menu_link_without_a_date_is_ignored(env):
    f = FakeFetcher(listing([(U9, T9)]), env)
    r = refresh.run("prices_test.csv", fetcher=f)
    assert r["new_links"] == 1
