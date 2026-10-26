"""Check the built page before publishing.

    python check.py            static checks on index.html, plus a browser check if Playwright is installed
    python check.py --links    also opens every outside link and reports any that do not answer 200

The browser check serves this folder, opens index.html at laptop (1280 px) and phone (390 px) width,
reports console errors and sideways scrolling, and saves screenshots to build/shots/.
Install the browser check once with:  pip install playwright  then  python -m playwright install chromium
"""
from __future__ import annotations

import http.server
import re
import socketserver
import sys
import threading
import urllib.request
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "index.html"


def static_checks(page: str) -> list[str]:
    issues = []
    for src in re.findall(r'(?:src|href)="(assets/[^"]+)"', page):
        if not (ROOT / src).exists():
            issues.append(f"Missing file: {src}")
    for anchor in set(re.findall(r'href="#([\w-]+)"', page)):
        if f'id="{anchor}"' not in page:
            issues.append(f'Broken in-page link: #{anchor}')
    return issues


def link_checks(page: str) -> list[str]:
    issues = []
    for url in sorted(set(re.findall(r'href="(https://[^"]+)"', page))):
        if "fonts.g" in url:
            continue
        try:
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0 link-check"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.status
        except Exception as err:  # noqa: BLE001 - report any failure as a broken link
            code = getattr(err, "code", str(err))
        if code == 999 and "linkedin.com" in url:
            print(f"  link {code}  {url}  (LinkedIn blocks automated checks; open it by hand once)")
            continue
        if code != 200:
            issues.append(f"{url} answered {code}")
        print(f"  link {code}  {url}")
    return issues


def browser_checks() -> list[str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Browser check skipped: Playwright is not installed (see the top of check.py).")
        return []
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):  # keep the check output short
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    shots = ROOT / "build" / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    issues = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for label, width, height in (("laptop", 1280, 900), ("phone", 390, 844)):
                page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
                errors = []
                page.on("console", lambda m, e=errors: e.append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda err, e=errors: e.append(str(err)))
                page.goto(f"http://127.0.0.1:{port}/index.html", wait_until="networkidle")
                page.wait_for_timeout(800)
                if page.evaluate("document.documentElement.scrollWidth") > width:
                    issues.append(f"{label}: the page scrolls sideways")
                issues += [f"{label}: console error: {e}" for e in errors]
                page.screenshot(path=str(shots / f"{label}.png"), full_page=True)
                page.close()
            browser.close()
        print(f"Screenshots saved in {shots}")
    finally:
        server.shutdown()
    return issues


def main() -> int:
    if not PAGE.exists():
        print("index.html is missing. Run: python build.py")
        return 1
    page = PAGE.read_text(encoding="utf-8")
    issues = static_checks(page)
    if "--links" in sys.argv:
        issues += link_checks(page)
    issues += browser_checks()
    if issues:
        print("Problems found:")
        for issue in issues:
            print("  -", issue)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
