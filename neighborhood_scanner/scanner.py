"""
Google Maps neighborhood scanner.
Visits lat/lon points, extracts visible business names,
takes screenshots, deduplicates against known dataset.
"""
import csv
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

# Fix console encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ensure the project root is on the path for imports
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from playwright.sync_api import sync_playwright
from neighborhood_scanner.dedup import DedupEngine

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "screenshots"
CHECKPOINT_FILE = BASE_DIR / "scan_checkpoint.json"
RESULTS_FILE = BASE_DIR / "scan_results.json"
DISCOVERIES_FILE = BASE_DIR / "discoveries.csv"
SCAN_DIR = BASE_DIR / "neighborhood_scanner"


class MapsScanner:
    def __init__(self, headless=False, viewport_width=1400, viewport_height=800):
        self.headless = headless
        self.viewport = {"width": viewport_width, "height": viewport_height}
        self.dedup = DedupEngine()
        self.browser = None
        self.context = None
        self.page = None

        # Results tracking
        self.results = []
        self.discoveries = []
        self.checkpoint = {}
        self._load_checkpoint()

    def start_browser(self):
        """Start a persistent headed Chromium session."""
        p = sync_playwright().start()
        self.browser = p.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        self.context = self.browser.new_context(
            viewport=self.viewport,
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
        print("Browser started (headed)")

    def close_browser(self):
        if self.browser:
            self.browser.close()

    def _load_checkpoint(self):
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, encoding="utf-8") as f:
                    self.checkpoint = json.load(f)
                print(f"Loaded checkpoint: {len(self.checkpoint.get('done', []))} targets done")
            except Exception:
                self.checkpoint = {}

    def _save_checkpoint(self):
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.checkpoint, f, indent=2)

    def _save_results(self):
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"results": self.results, "discoveries": self.discoveries}, f, indent=2)

        with open(DISCOVERIES_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "business_name", "source_lat", "source_lon", "zoom",
                "category", "phone", "website", "instagram", "facebook",
                "google_maps_cid", "confidence", "screenshot",
            ])
            w.writeheader()
            for d in self.discoveries:
                w.writerow(d)

    def handle_overlays(self, page):
        """Handle cookie consent, login prompts, and other overlays."""
        handled = False
        try:
            # Cookie consent buttons
            for selector in [
                'button:has-text("Accept all")',
                'button:has-text("Accept All")',
                'button:has-text("I agree")',
                'button:has-text("Agree")',
                'button[aria-label*="Accept"]',
                'div[role="dialog"] button:first-child',
            ]:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(1000)
                    handled = True
                    break
        except Exception:
            pass

        # Login prompt dismissal
        try:
            close_btn = page.query_selector('button[aria-label="Close"]')
            if close_btn and close_btn.is_visible():
                close_btn.click()
                page.wait_for_timeout(500)
                handled = True
        except Exception:
            pass

        return handled

    def extract_business_names(self, page):
        """Extract visible business names from the Maps page."""
        names = set()

        # Strategy 1: Map pins — look for labels near map markers
        try:
            for el in page.query_selector_all('[class*="fontBodyMedium"], [class*="place-name"], [class*="fontTitleSmall"]'):
                text = el.inner_text().strip()
                if 2 < len(text) < 80:
                    names.add(text)
        except Exception:
            pass

        # Strategy 2: Sidebar result items
        try:
            for el in page.query_selector_all('a[role="link"]'):
                aria = el.get_attribute("aria-label")
                if aria and 2 < len(aria) < 100:
                    names.add(aria.strip())
                text = el.inner_text().strip()
                if text and 2 < len(text) < 100:
                    names.add(text)
        except Exception:
            pass

        # Strategy 3: Article-style result cards
        try:
            for el in page.query_selector_all('div[role="article"]'):
                text = el.inner_text()
                if text:
                    for line in text.split("\n"):
                        line = line.strip()
                        if 3 < len(line) < 80 and not re.match(r'^\d', line):
                            names.add(line)
        except Exception:
            pass

        # Strategy 4: All visible text nodes in the results panel
        try:
            panel = page.query_selector('[role="main"]')
            if panel:
                text = panel.inner_text()
                for line in text.split("\n"):
                    line = line.strip()
                    if 3 < len(line) < 80 and not re.match(r'^[\d\s\+\-\(\)\/★☆\.]+$', line):
                        names.add(line)
        except Exception:
            pass

        return names

    def is_business_name(self, name):
        """Filter out non-business text like UI labels (English + Spanish)."""
        skip = [
            "directions", "save", "nearby", "search here", "zoom in", "zoom out",
            "satellite", "map", "traffic", "transit", "bicycling", "street view",
            "send to phone", "share", "reviews", "overview", "photos", "about",
            "menu", "reserve a table", "order online", "website", "call",
            "people also search for", "people also viewed", "you might also like",
            "your lists", "contribute", "updates", "settings", "help", "feedback",
            "privacy", "terms", "sign in", "sign out",
            # Spanish UI labels
            "etiquetas", "restaurantes", "hoteles", "farmacias", "museos",
            "cajeros automáticos", "cosas que hacer", "esta área",
            "vista con el globo terráqueo", "estaciones de transporte público",
            "transporte", "alojamiento", "compras", "ocio", "vida nocturna",
            "atracciones", "servicios", "comida", "bebidas",
            "cómo llegar", "guardar", "tus listas",
            "contribuir", "compartir", "enviar al teléfono",
            "reseñas", "fotos", "información general",
            # Generic non-business labels
            "km", "°", "temperatura", "weather", "a few clouds",
            "clear", "cloudy", "rain", "sunny", "mostly cloudy",
        ]
        n = name.lower().strip()
        if len(n) < 3 or len(n) > 80:
            return False
        if any(s in n for s in skip):
            return False
        if re.match(r'^[\d\s\+\-\(\)]+$', n):
            return False
        if re.match(r'^[★☆\d\.\/°\s]+$', n):
            return False
        # Single common words
        if n in ("labels", "map", "traffic", "transit", "bike", "terrain",
                 "restaurants", "hotels", "pharmacies", "museums", "atm"):
            return False
        return True

    def scan_target(self, lat, lon, zoom=16):
        """Visit a single target coordinate and extract business names."""
        target_id = f"{lat}_{lon}_z{zoom}"
        if target_id in self.checkpoint.get("done", []):
            return None

        url = f"https://www.google.com/maps/@{lat},{lon},{zoom}z?hl=en"
        print(f"\n  [{target_id}] {url}")
        result = {
            "target_id": target_id,
            "latitude": lat,
            "longitude": lon,
            "zoom": zoom,
            "url": url,
            "success": False,
            "names_found": [],
            "new_discoveries": [],
            "screenshot": None,
            "error": None,
        }

        try:
            # Maps is a SPA — don't wait for networkidle, it never settles
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_timeout(5000)

            # Handle any overlays
            self.handle_overlays(self.page)

            # Wait for map content to render (look for canvas or sidebar)
            try:
                self.page.wait_for_selector("canvas[aria-label*='Map']", timeout=15000)
                self.page.wait_for_timeout(2000)
            except Exception:
                # Try alternative — wait for any link to appear
                try:
                    self.page.wait_for_selector('a[role="link"]', timeout=10000)
                except Exception:
                    pass

            # Take screenshot
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            ss_name = f"scan_{lat}_{lon}_z{zoom}.png"
            ss_path = OUTPUT_DIR / ss_name
            self.page.screenshot(path=str(ss_path), full_page=False)
            result["screenshot"] = ss_name

            # Extract names
            raw_names = self.extract_business_names(self.page)
            filtered = [n for n in raw_names if self.is_business_name(n)]
            result["names_found"] = filtered

            # Dedup
            for name in filtered:
                known_as = self.dedup.is_known(name)
                if known_as:
                    print(f"    Known: {name} -- {known_as}")
                else:
                    print(f"    NEW DISCOVERY: {name}")
                    discovery = {
                        "business_name": name,
                        "source_lat": lat,
                        "source_lon": lon,
                        "zoom": zoom,
                        "category": "",
                        "phone": "",
                        "website": "",
                        "instagram": "",
                        "facebook": "",
                        "google_maps_cid": "",
                        "confidence": "candidate",
                        "screenshot": ss_name,
                    }
                    self.discoveries.append(discovery)
                    result["new_discoveries"].append(name)

            result["success"] = True

        except Exception as e:
            result["error"] = str(e)
            print(f"    ERROR: {e}")
            # Even on error, try a screenshot
            try:
                ss_name = f"scan_{lat}_{lon}_z{zoom}_error.png"
                ss_path = OUTPUT_DIR / ss_name
                self.page.screenshot(path=str(ss_path), full_page=False)
                result["screenshot"] = ss_name
            except Exception:
                pass

        self.results.append(result)
        return result

    def run(self, targets, start_at=0, batch_size=10):
        """Run scanner over a list of targets with checkpointing."""
        self.dedup.load()

        done_count = len(self.checkpoint.get("done", []))
        total = len(targets)

        print(f"\nScanning {total} targets ({done_count} already done)")
        print(f"Start at index: {start_at}")

        for i, target in enumerate(targets[start_at:]):
            idx = start_at + i
            lat = float(target["latitude"])
            lon = float(target["longitude"])
            zoom = 17 if str(target.get("z17", "")).lower() == "yes" else 16

            target_id = f"{lat}_{lon}_z{zoom}"
            if target_id in self.checkpoint.get("done", []):
                continue

            result = self.scan_target(lat, lon, zoom)
            if result is None:
                continue

            # Checkpoint every batch_size
            done_list = self.checkpoint.setdefault("done", [])
            done_list.append(target_id)
            new_found = len(result.get("new_discoveries", []))

            print(f"  [{idx + 1}/{total}] {lat},{lon} z{zoom} — "
                  f"{len(result['names_found'])} names, {new_found} new")

            if (idx + 1) % batch_size == 0:
                self._save_checkpoint()
                self._save_results()
                print(f"  [CHECKPOINT] Saved at {idx + 1}/{total}")

            # Polite delay between scans (8-10s)
            if idx < total - 1:
                delay = 8 + (hash(str(lat)) % 3)
                print(f"  Waiting {delay}s...")
                time.sleep(delay)

        # Final save
        self._save_checkpoint()
        self._save_results()

        total_new = len(self.discoveries)
        print(f"\n{'='*50}")
        print(f"SCAN COMPLETE")
        print(f"{'='*50}")
        print(f"  Targets scanned: {len(self.results)}")
        print(f"  New discoveries: {total_new}")
        print(f"  Screenshots:     {OUTPUT_DIR}")
        print(f"  Results:         {RESULTS_FILE}")
        print(f"  Discoveries CSV: {DISCOVERIES_FILE}")


def load_targets():
    """Load scan targets from CSV with multiple fallback paths."""
    paths = [
        SCAN_DIR / "scan_targets.csv",
        Path("scan_targets.csv"),
    ]
    for p in paths:
        if p.exists():
            with open(p, encoding="utf-8-sig", newline="") as f:
                return list(csv.DictReader(f))
    raise FileNotFoundError("No scan_targets.csv found")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Google Maps Neighborhood Scanner")
    parser.add_argument("--headless", action="store_true", help="Run headless (no GUI)")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--limit", type=int, default=10, help="Max targets to scan")
    args = parser.parse_args()

    targets = load_targets()

    if args.limit and args.limit < len(targets):
        targets = targets[:args.limit]

    scanner = MapsScanner(headless=False)
    try:
        scanner.start_browser()
        scanner.run(targets, start_at=args.start)
    finally:
        scanner.close_browser()


if __name__ == "__main__":
    main()
