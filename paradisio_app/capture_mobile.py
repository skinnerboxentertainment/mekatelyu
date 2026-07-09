"""
Capture Paradisio Board at mobile viewport sizes using Playwright.
Saves screenshots to docs/paradisio_app/screenshots/mobile/ for Codex visual review.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "docs" / "paradisio_app"
OUTPUT_DIR = APP_DIR / "screenshots" / "mobile"

VIEWPORTS = [
    {"name": "iphone_se", "width": 375, "height": 667},
    {"name": "iphone_12", "width": 390, "height": 844},
    {"name": "pixel_5", "width": 393, "height": 851},
    {"name": "iphone_pro_max", "width": 430, "height": 932},
]

INDEX_URL = APP_DIR.resolve().as_uri() + "/index.html"


async def capture_business_page(page, viewport, biz_slug):
    url = APP_DIR.resolve().as_uri() + f"/businesses/{biz_slug}.html"
    await page.goto(url, wait_until="networkidle")
    await asyncio.sleep(1)
    path = OUTPUT_DIR / "business" / f"{biz_slug}_{viewport['name']}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(path), full_page=True)
    return path


async def capture_homepage(page, viewport, query=""):
    await page.goto(INDEX_URL, wait_until="networkidle")
    await asyncio.sleep(1.5)
    if query:
        await page.fill("#search", query)
        await asyncio.sleep(0.5)
    path = OUTPUT_DIR / "home" / f"{'search_' + query.replace(' ','_') if query else 'default'}_{viewport['name']}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(path), full_page=True)
    return path


async def capture_filter_state(page, viewport):
    """Capture homepage with specific filters applied."""
    await page.goto(INDEX_URL, wait_until="networkidle")
    await asyncio.sleep(1.5)
    # Select WhatsApp filter
    await page.select_option("#channel-filter", "whatsapp")
    await asyncio.sleep(0.5)
    path = OUTPUT_DIR / "home" / f"filter_whatsapp_{viewport['name']}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(path), full_page=True)

    # Select a category
    await page.select_option("#category-filter", "restaurant")
    await asyncio.sleep(0.5)
    path = OUTPUT_DIR / "home" / f"filter_restaurant_{viewport['name']}.png"
    await page.screenshot(path=str(path), full_page=True)
    return path


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "home").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "business").mkdir(parents=True, exist_ok=True)

    # Pick a sample business with good data
    with open(APP_DIR / "data" / "businesses.json") as f:
        businesses = json.load(f)
    sample = None
    for b in businesses:
        if b["channels"]["whatsapp"] and b["channels"]["instagram"] and b["lat"] and b["lng"]:
            sample = b
            break
    if not sample:
        sample = businesses[0]

    print(f"Sample business: {sample['name']} ({sample['slug']})")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        pages_captured = 0

        for vp in VIEWPORTS:
            context = await browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                device_scale_factor=2,
                is_mobile=True,
                locale="en-US",
            )
            page = await context.new_page()

            # Homepage default
            p1 = await capture_homepage(page, vp)
            print(f"  Home (default) {vp['name']} -> {p1.name}")
            pages_captured += 1

            # Homepage with search
            p2 = await capture_homepage(page, vp, query="cacao")
            print(f"  Home (search)  {vp['name']} -> {p2.name}")
            pages_captured += 1

            # Homepage with filters
            try:
                await capture_filter_state(page, vp)
                print(f"  Home (filters) {vp['name']} captured")
                pages_captured += 1
            except Exception as e:
                print(f"  Home (filters) {vp['name']} error: {e}")

            await context.close()

            # Business page in separate context to avoid filter state
            context2 = await browser.new_context(
                viewport={"width": vp["width"], "height": vp["height"]},
                device_scale_factor=2,
                is_mobile=True,
                locale="en-US",
            )
            page2 = await context2.new_page()
            p3 = await capture_business_page(page2, vp, sample["slug"])
            print(f"  Biz page      {vp['name']} -> {p3.name}")
            pages_captured += 1
            await context2.close()

        await browser.close()

    print(f"\nDone. {pages_captured} screenshots captured in {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
