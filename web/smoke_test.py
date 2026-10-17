#!/usr/bin/env python3
"""Check a deployed or local Price Signal service without browser automation.

    python3 web/smoke_test.py https://YOUR-SERVICE.onrender.com
    python3 web/smoke_test.py http://127.0.0.1:5000

The first request allows extra time for a free Render service to wake. The test
checks public pages, JSON health/status endpoints and the current safety state;
it never requires estimates to be visible when the guard correctly withholds them.
"""
import argparse
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

PAGES = {
    "/": "Sri Lanka Food Price Signal",
    "/today": "Today’s price guide",
    "/explore": "Explore past prices",
    "/report": "Weekly report",
    "/method": "How Price Signal works",
    "/help": "Help and support",
}
VALID_STATES = {"ok", "stale", "report_not_read", "source_unavailable"}


def fetch(base, path, timeout, attempts=2):
    url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
    last = None
    for attempt in range(attempts):
        try:
            req = Request(url, headers={"User-Agent": "price-signal-smoke/1.0"})
            with urlopen(req, timeout=timeout) as response:
                return response.status, response.headers, response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(3)
    raise RuntimeError(f"{url} could not be read: {last}")


def run(base, timeout=75):
    checks = []
    status, headers, body = fetch(base, "/healthz", timeout)
    health = json.loads(body)
    checks.append(("/healthz", status == 200 and health == {"ok": True}, str(health)))

    status, headers, body = fetch(base, "/api/status", timeout)
    state = json.loads(body)
    valid_status = (status == 200 and state.get("state") in VALID_STATES
                    and bool(state.get("report_date")) and bool(state.get("today")))
    checks.append(("/api/status", valid_status,
                   f"state={state.get('state')} report={state.get('report_date')} today={state.get('today')}"))

    for path, phrase in PAGES.items():
        status, headers, body = fetch(base, path, timeout)
        text = body.decode("utf-8", errors="replace")
        html = headers.get_content_type() == "text/html"
        checks.append((path, status == 200 and html and phrase in text,
                       f"status={status} html={html} marker={phrase!r}"))
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", help="deployed or local base URL")
    parser.add_argument("--timeout", type=int, default=75,
                        help="seconds allowed for each request (default: 75 for free-tier wake-up)")
    args = parser.parse_args(argv)
    checks = run(args.base_url, args.timeout)
    failed = 0
    for path, ok, detail in checks:
        print(("PASS" if ok else "FAIL") + f" {path:<12} {detail}")
        failed += not ok
    print(f"{len(checks) - failed}/{len(checks)} public checks passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
