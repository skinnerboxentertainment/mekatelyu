"""Capture mobile screenshots of live whappin.com business pages for QA ticket tickets.

Reads a list of issue numbers from GitHub (or a provided JSON file) and captures
an iPhone-12-sized (390x844, 2x scale) full-page screenshot of each page whose
slug appears in the ticket title.

Usage:
    python scripts/capture_ticket_screenshots.py --issues 77 76 75
    python scripts/capture_ticket_screenshots.py --all-closed
    python scripts/capture_ticket_screenshots.py --slugs-file issues.json

Saves PNGs to audit/qa-triage/screenshots/mobile/{issue}_{slug}.png
"""

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

REPO = "skinnerboxentertainment/mekatelyu"
BASE_URL = "https://www.whappin.com"
VIEWPORT = {"name": "iphone_12", "width": 390, "height": 844}

SLUG_ALIASES = {
    "casa-lily-cocles": "casa-lily-playa-chiquita",
    "casa-olingo-playa-negra": "casa-olingo-cocles",
    "casa-canopy-cocles": "casa-canopy-playa-chiquita",
    "caf-jaguar-art-gallery-cocles": "caf-jaguar-art-gallery-playa-chiquita",
}

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "audit" / "qa-triage" / "screenshots" / "mobile"


def gh_json(args: list) -> list:
    out = subprocess.run(
        ["gh", *args, "--json", "number,title,state", "--jq", "."],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise RuntimeError(f"gh failed: {out.stderr}")
    return json.loads(out.stdout)


def load_issues(args) -> list[dict]:
    if args.slugs_file:
        with open(args.slugs_file, encoding="utf-8") as f:
            return json.load(f)
    if args.all_closed:
        return gh_json(["issue", "list", "--repo", REPO, "--state", "closed", "--limit", "100"])
    return [{"number": n, "title": f"QA: {s}"} for n, s in args.pairs]


def slug_from_title(title: str) -> str:
    t = title.strip()
    if t.lower().startswith("qa:"):
        t = t[3:].strip()
    slug = t.strip()
    return SLUG_ALIASES.get(slug, slug)


async def capture(slug: str, out_path: Path, playwright) -> bool:
    url = f"{BASE_URL}/businesses/{slug}.html"
    try:
        browser = await playwright.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": VIEWPORT["width"], "height": VIEWPORT["height"]},
            device_scale_factor=2,
            is_mobile=True,
            locale="en-US",
        )
        page = await ctx.new_page()
        resp = await page.goto(url, wait_until="networkidle", timeout=60000)
        if resp is None or resp.status >= 400:
            print(f"  SKIP {slug}: HTTP {resp.status if resp else 'no response'}")
            await browser.close()
            return False
        await page.wait_for_timeout(1200)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(out_path), full_page=True)
        await browser.close()
        return True
    except Exception as e:
        print(f"  ERROR {slug}: {e}")
        try:
            await browser.close()
        except Exception:
            pass
        return False


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", nargs="*", type=int, help="Issue numbers to capture")
    ap.add_argument("--all-closed", action="store_true")
    ap.add_argument("--slugs-file", help="JSON file with [{number, title}]")
    ap.add_argument("--dry-run", action="store_true", help="Print URLs without capturing")
    args = ap.parse_args()

    if args.issues:
        issues = []
        for n in args.issues:
            r = subprocess.run(
                ["gh", "issue", "view", str(n), "--repo", REPO, "--json", "number,title,state"],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                print(f"  WARN issue #{n} not found: {r.stderr.strip()}")
                continue
            issues.append(json.loads(r.stdout))
    else:
        issues = load_issues(args)

    targets = []
    for i in issues:
        slug = slug_from_title(i["title"])
        if not slug:
            print(f"  WARN issue #{i['number']}: empty slug from title {i['title']!r}")
            continue
        targets.append((i["number"], slug))

    print(f"Targets: {len(targets)}")
    for n, slug in targets:
        print(f"  #{n} -> {BASE_URL}/businesses/{slug}.html")

    if args.dry_run:
        return

    ok = 0
    fail = []
    async with async_playwright() as p:
        for n, slug in targets:
            out = OUTPUT_DIR / f"{n}_{slug}.png"
            if await capture(slug, out, p):
                print(f"  OK  #{n} {slug} -> {out.relative_to(ROOT)}")
                ok += 1
            else:
                fail.append((n, slug))
                print(f"  FAIL #{n} {slug}")

    print(f"\nDone: {ok} captured, {len(fail)} failed in {OUTPUT_DIR}")
    for n, slug in fail:
        print(f"  FAILED #{n}: {slug}")


if __name__ == "__main__":
    asyncio.run(main())
