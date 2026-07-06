"""
Playwright-based Google Maps neighborhood scanner.
Opens each known business CID, extracts nearby business names from the sidebar.
"""
import csv
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from playwright.sync_api import sync_playwright
from neighborhood_scanner.dedup import DedupEngine

BASE_DIR = Path(__file__).parent.parent
MASTER_CSV = BASE_DIR / "pv_within_5km_enriched_b.csv"
ADDITIONS_CSV = BASE_DIR / "pv_within_5km_verified_additions_enriched.csv"
OUTPUT_DIR = BASE_DIR / "screenshots"
CHECKPOINT_FILE = BASE_DIR / "scan_checkpoint.json"
RESULTS_FILE = BASE_DIR / "scan_results.json"
DISCOVERIES_FILE = BASE_DIR / "discoveries.csv"

DELAY_MIN, DELAY_MAX = 8, 12


class CIDScanner:
    def __init__(self, headless=False):
        self.headless = headless
        self.dedup = DedupEngine()
        self.browser = None
        self.context = None
        self.page = None
        self.results = []
        self.discoveries = []
        self.checkpoint = self._load_checkpoint()

    def _load_checkpoint(self):
        try:
            with open(CHECKPOINT_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_checkpoint(self):
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.checkpoint, f, indent=2)

    def _save_results(self):
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"results": self.results, "discoveries": self.discoveries}, f, indent=2)
        with open(DISCOVERIES_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "business_name", "source_business", "source_cid",
                "source_lat", "source_lon", "phone", "website",
                "instagram", "google_maps_cid", "confidence", "screenshot",
            ])
            w.writeheader()
            for d in self.discoveries:
                w.writerow(d)

    def start_browser(self):
        p = sync_playwright().start()
        self.browser = p.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
            ],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1400, "height": 800},
            locale="en-US",
            timezone_id="America/Costa_Rica",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            ),
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(30000)
        print("Browser started")

    def close_browser(self):
        if self.browser:
            self.browser.close()

    def handle_overlays(self):
        """Dismiss cookie consent, login prompts."""
        try:
            for selector in [
                'button:has-text("Accept all")',
                'button:has-text("Accept All")',
                'button:has-text("I agree")',
                'button:has-text("Agree")',
                'button[aria-label*="Accept"]',
                'button[aria-label="Close"]',
                'form button:has-text("Accept")',
            ]:
                btn = self.page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click()
                    self.page.wait_for_timeout(1000)
                    break
        except Exception:
            pass

    def extract_sidebar_names(self):
        """Extract business names from the sidebar/nearby panel."""
        names = set()
        try:
            # All link elements with aria-labels (most reliable for business names)
            for el in self.page.query_selector_all('a[role="link"]'):
                aria = el.get_attribute("aria-label")
                if aria:
                    aria = aria.strip()
                    if 3 < len(aria) < 100 and self._is_business_name(aria):
                        names.add(aria)
                text = el.inner_text().strip()
                if text and 3 < len(text) < 100 and self._is_business_name(text):
                    names.add(text)
        except Exception:
            pass

        # Nearby/result items
        try:
            for el in self.page.query_selector_all('[class*="result"], [class*="nearby"], [class*="listing"]'):
                text = el.inner_text().strip()
                if text and 3 < len(text) < 100 and self._is_business_name(text):
                    for line in text.split("\n"):
                        line = line.strip()
                        if 3 < len(line) < 80 and self._is_business_name(line):
                            names.add(line)
        except Exception:
            pass

        return names

    def _is_business_name(self, name):
        n = name.lower().strip()
        if len(n) < 3 or len(n) > 80:
            return False
        skip = [
            "directions", "save", "nearby", "search here", "zoom", "satellite",
            "map", "traffic", "transit", "bike", "street view", "send to phone",
            "share", "reviews", "overview", "photos", "about", "menu",
            "reserve a table", "order online", "website", "call",
            "people also search for", "people also viewed", "you might also like",
            "your lists", "contribute", "updates", "settings", "help", "feedback",
            "privacy", "terms", "sign in", "sign out", "report a problem",
            "data", "send feedback", "kilometers", "km", "meter", "m",
            "things to do", "globe view", "atms", "labels",
            "restaurants", "hotels", "pharmacies", "museums", "atm",
            "reviews", "write a review", "add a photo", "know this place?",
            # Spanish
            "etiquetas", "restaurantes", "hoteles", "farmacias", "museos",
            "cajeros autom", "cosas que hacer", "esta area",
            "vista con el globo", "estaciones de transporte",
            # Short generic
            "sign in", "sign out", "support", "help",
        ]
        if any(s in n for s in skip):
            return False
        if re.match(r'^[\d\s\+\-\(\)\u00b0\/\.,]+$', n):
            return False
        return True

    def scan_cid(self, row):
        """Scan one CID: open Maps, extract nearby names, screenshot."""
        cid = row.get("google_maps_cid", "").strip()
        name = row.get("business_name", "").strip()
        lat = row.get("latitude", "")
        lon = row.get("longitude", "")

        target_id = f"cid_{cid}" if cid else f"pin_{lat}_{lon}"

        if target_id in self.checkpoint.get("done", []):
            return None

        url = f"https://www.google.com/maps?cid={cid}" if cid else f"https://www.google.com/maps/@{lat},{lon},17z?hl=en"
        print(f"\n  [{target_id}] {name}")

        result = {
            "target_id": target_id,
            "source_name": name,
            "source_cid": cid,
            "source_lat": lat,
            "source_lon": lon,
            "url": url,
            "success": False,
            "names_found": [],
            "new_discoveries": [],
            "screenshot": None,
            "error": None,
        }

        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_timeout(5000)

            self.handle_overlays()

            # Wait for the place card or map to render
            try:
                self.page.wait_for_selector("canvas", timeout=10000)
                self.page.wait_for_timeout(3000)
            except Exception:
                pass

            # Scroll the sidebar to trigger lazy loading
            try:
                panel = self.page.query_selector('[role="main"], [aria-label*="Results"], [aria-label*="sidebar"]')
                if panel:
                    self.page.evaluate("el => el.scrollTop = el.scrollHeight", panel)
                    self.page.wait_for_timeout(2000)
            except Exception:
                pass

            # Screenshot
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            ss_name = f"cid_{cid or 'pin'}_{name[:20].replace(' ', '_')}.png"
            ss_path = OUTPUT_DIR / ss_name
            self.page.screenshot(path=str(ss_path), full_page=False)
            result["screenshot"] = ss_name

            # Extract names
            raw = self.extract_sidebar_names()
            result["names_found"] = list(raw)

            for business_name in raw:
                known_as = self.dedup.is_known(business_name)
                if known_as:
                    print(f"    Known: {business_name[:50]}")
                else:
                    print(f"    NEW: {business_name[:50]}")
                    self.discoveries.append({
                        "business_name": business_name,
                        "source_business": name,
                        "source_cid": cid,
                        "source_lat": lat,
                        "source_lon": lon,
                        "phone": "",
                        "website": "",
                        "instagram": "",
                        "google_maps_cid": "",
                        "confidence": "candidate",
                        "screenshot": ss_name,
                    })
                    result["new_discoveries"].append(business_name)

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            print(f"    ERROR: {e}")
            try:
                ss_name = f"cid_{cid or 'pin'}_{name[:20].replace(' ', '_')}_error.png"
                self.page.screenshot(path=str(OUTPUT_DIR / ss_name), full_page=False)
                result["screenshot"] = ss_name
            except Exception:
                pass

        self.results.append(result)
        return result

    def run(self, limit=None):
        """Run the scanner over all businesses with CIDs (or all)."""
        self.dedup.load()

        # Load source data
        rows = []
        for csv_path in [MASTER_CSV, ADDITIONS_CSV]:
            try:
                with open(csv_path, encoding="utf-8-sig", newline="") as f:
                    for row in csv.DictReader(f):
                        cid = (row.get("google_maps_cid") or "").strip()
                        if cid:
                            rows.append(row)
            except FileNotFoundError:
                pass

        # Also include rows without CID but with coordinates
        all_biz = list(rows)
        for csv_path in [MASTER_CSV, ADDITIONS_CSV]:
            try:
                with open(csv_path, encoding="utf-8-sig", newline="") as f:
                    for row in csv.DictReader(f):
                        cid = (row.get("google_maps_cid") or "").strip()
                        lat = (row.get("latitude") or "").strip()
                        if not cid and lat:
                            all_biz.append(row)
            except FileNotFoundError:
                pass

        if limit:
            all_biz = all_biz[:limit]

        done_count = len(self.checkpoint.get("done", []))
        print(f"Scan targets: {len(all_biz)} ({done_count} already done)")

        for i, row in enumerate(all_biz):
            target_id = f"cid_{row.get('google_maps_cid','').strip() or 'pin'}"
            if target_id in self.checkpoint.get("done", []):
                continue

            result = self.scan_cid(row)
            if result is None:
                continue

            done_list = self.checkpoint.setdefault("done", [])
            done_list.append(target_id)
            new_count = len(result.get("new_discoveries", []))

            print(f"  [{i + 1}/{len(all_biz)}] {new_count} new discoveries")

            # Checkpoint every 10
            if (len(done_list)) % 10 == 0:
                self._save_checkpoint()
                self._save_results()
                print(f"  [CHECKPOINT] {len(done_list)}/{len(all_biz)} done")

            # Polite delay
            delay = DELAY_MIN + (hash(str(target_id)) % (DELAY_MAX - DELAY_MIN))
            print(f"  Waiting {delay}s...")
            time.sleep(delay)

        self._save_checkpoint()
        self._save_results()
        print(f"\nDONE. {len(self.discoveries)} new discoveries across {len(self.results)} scans")
        print(f"Discoveries: {DISCOVERIES_FILE}")
        print(f"Screenshots: {OUTPUT_DIR}/")


def load_cids():
    """Load businesses with CIDs."""
    rows = []
    for csv_path in [MASTER_CSV, ADDITIONS_CSV]:
        try:
            with open(csv_path, encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    cid = (row.get("google_maps_cid") or "").strip()
                    if cid:
                        rows.append(row)
        except FileNotFoundError:
            pass
    return rows


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Max scans to run")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()

    scanner = CIDScanner(headless=args.headless)
    try:
        scanner.start_browser()
        scanner.run(limit=args.limit)
    finally:
        scanner.close_browser()
