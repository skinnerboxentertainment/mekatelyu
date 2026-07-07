"""
Slow stealth Google search — resolves business names to Maps CIDs + coordinates.
Uses real installed Chrome with persistent profile for human-like browsing.
"""
import csv
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import subprocess

from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent
SCREENSHOTS_DIR = BASE / "stealth_screenshots"
CHECKPOINT_FILE = BASE / "stealth_checkpoint.json"
RESULTS_FILE = BASE / "stealth_results.jsonl"
PROFILE_DIR = BASE / "profiles" / "chrome_pv_google"
LOG_FILE = BASE / "stealth_session.log"
TARGETS = BASE / "stealth_targets.csv"

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9222

# Pacing
MIN_DELAY = 25
MAX_DELAY = 45
SESSION_MAX = 30
REST_MINUTES = 10


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def extract_from_maps_url(url):
    """Extract CID (from hex), lat, lon from a Google Maps URL."""
    result = {"cid": "", "lat": "", "lon": ""}

    # CID from !1s0xHEX:0xHEX! — second hex is decimal CID
    m = re.search(r'!1s0x[a-f0-9]+:0x([a-f0-9]+)', url, re.I)
    if m:
        result["cid"] = str(int(m.group(1), 16))

    # CID from ?cid= or &cid=
    if not result["cid"]:
        m = re.search(r'[?&]cid=(\d{10,})', url)
        if m:
            result["cid"] = m.group(1)

    # Coordinates from !3dLAT!4dLON (actual place coords, not viewport)
    m = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if m:
        result["lat"] = m.group(1)
        result["lon"] = m.group(2)
    # Fallback: coordinates from @lat,lon (viewport center — less reliable)
    if not result["lat"] or not result["lon"]:
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if m:
            result["lat"] = m.group(1)
            result["lon"] = m.group(2)

    return result


def detect_captcha(page):
    """Check if Google served a CAPTCHA or unusual traffic page."""
    try:
        title = page.title().lower()
        url = page.url.lower()
        body = page.inner_text("body").lower()[:500]
        if "unusual traffic" in body or "captcha" in body or "sorry" in body:
            return True
        if "sorry" in title or "captcha" in title:
            return True
        if "consent" in url and "google.com" in url:
            return False  # Just a consent dialog, not CAPTCHA
    except:
        pass
    return False


PV_CENTER_LAT = 9.655
PV_CENTER_LON = -82.753
PV_RADIUS_DEG = 0.045  # ~5km in lat/lon


def in_pv_area(lat, lon):
    """Check if coordinates fall within ~5km of Puerto Viejo center."""
    try:
        lat_f, lon_f = float(lat), float(lon)
        return (
            abs(lat_f - PV_CENTER_LAT) <= PV_RADIUS_DEG
            and abs(lon_f - PV_CENTER_LON) <= PV_RADIUS_DEG
        )
    except (ValueError, TypeError):
        return False


def search_and_resolve(page, name, lat_hint="", lon_hint=""):
    """Search Google Maps directly for a business, extract CID, coords, phone, website."""
    result = {
        "business_name": name,
        "query": f'"{name}" Puerto Viejo',
        "maps_url": "",
        "cid": "",
        "cid_source": "",
        "latitude": "",
        "longitude": "",
        "phone": "",
        "website": "",
        "confidence": "low",
        "screenshot": "",
        "error": "",
        "success": False,
    }

    try:
        q = f'{name} Puerto Viejo'
        search_url = f"https://www.google.com/maps?q={q.replace(' ', '+')}"
        log(f"  Searching Maps: {name[:50]}")
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        # Randomized dwell for Maps to load & potentially redirect to place page
        time.sleep(random.uniform(5, 12))

        # Light CAPTCHA check (less common on Maps, but still possible)
        if detect_captcha(page):
            result["error"] = "CAPTCHA or unusual traffic detected"
            log(f"  CAPTCHA detected — stopping session")
            return result

        # If a single place resolved, Maps redirects to /place/ URL automatically
        final_url = page.url

        # If still on /search/ URL, try clicking the first result
        if "/search/" in final_url:
            log(f"  Search results page — trying first result")
            first_result = page.query_selector('a[href*="/place/"]')
            if first_result:
                try:
                    with page.expect_navigation(timeout=15000):
                        first_result.click()
                    time.sleep(random.uniform(3, 7))
                    final_url = page.url
                except:
                    pass

        # Extract data from final URL
        extracted = extract_from_maps_url(final_url)
        result["maps_url"] = final_url.split("&")[0]
        result["cid"] = extracted["cid"]
        result["cid_source"] = "hex_feature_id" if extracted["cid"] and "!1s" in final_url else "url_param" if extracted["cid"] else ""
        result["latitude"] = extracted["lat"]
        result["longitude"] = extracted["lon"]

        # Try to extract phone from the place card
        try:
            tel = page.query_selector('a[href^="tel:"]')
            if tel:
                result["phone"] = (tel.get_attribute("href") or "").replace("tel:", "")
        except:
            pass

        # Try to extract website from the place card
        try:
            web = page.query_selector('a[data-item-id="authority"], button:has-text("Website")')
            if web:
                result["website"] = web.get_attribute("href") or ""
        except:
            pass

        # Confidence
        has_cid = bool(result["cid"])
        has_coords = bool(result["latitude"] and result["longitude"])
        in_zone = has_coords and in_pv_area(result["latitude"], result["longitude"])
        if has_cid and in_zone:
            result["confidence"] = "high"
        elif has_cid and has_coords and not in_zone:
            result["confidence"] = "low"
            if not result["error"]:
                result["error"] = f"Outside PV zone: {result['latitude']},{result['longitude']}"
        elif has_cid or (has_coords and in_zone):
            result["confidence"] = "medium"
        elif "/place/" in final_url:
            result["confidence"] = "medium"
        else:
            result["confidence"] = "low"

        result["success"] = True

    except Exception as e:
        result["error"] = str(e)[:120]

    # Screenshot (even on failure)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]", "_", name[:30])
    ss_name = f"{slug}.png"
    try:
        page.screenshot(path=str(SCREENSHOTS_DIR / ss_name), full_page=False)
        result["screenshot"] = ss_name
    except:
        pass

    return result


def main():
    print("=" * 60)
    print("SLOW STEALTH GOOGLE SEARCH")
    print("=" * 60)

    # Load checkpoint
    checkpoint = {"done": [], "session_count": 0, "last_run": ""}
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, encoding="utf-8") as f:
                checkpoint = json.load(f)
            log(f"Loaded checkpoint: {len(checkpoint.get('done', []))} done, "
                f"{checkpoint.get('session_count', 0)} sessions")
        except:
            pass

    # Determine next session number
    session_num = checkpoint.get("session_count", 0) + 1
    done_set = set(checkpoint.get("done", []))

    # Load targets
    targets = []
    with open(TARGETS, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("business_name") or "").strip()
            if name and row.get("source") != "done":
                targets.append(row)

    remaining = [t for t in targets if t["business_name"] not in done_set]
    log(f"Targets: {len(targets)} total, {len(done_set)} done, "
        f"{len(remaining)} remaining (session {session_num})")

    if not remaining:
        log("All targets complete!")
        return

    # Cap this session
    batch = remaining[:SESSION_MAX]
    log(f"This session: {len(batch)} searches")

    # Kill any leftover Chrome on our CDP port from previous crashed sessions
    result = subprocess.run(
        ["netstat", "-ano"], capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if f":{CDP_PORT}" in line and "LISTENING" in line:
            parts = line.strip().split()
            if parts:
                pid = parts[-1]
                subprocess.run(["taskkill", "/F", "/PID", pid],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)

    # Launch real Chrome manually with CDP — no Playwright automation flags
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Profile: {PROFILE_DIR}")

    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    log("Chrome launched, connecting via CDP...")
    time.sleep(3)

    p = sync_playwright().start()
    try:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        # Use existing tab or create new one
        if browser.contexts and browser.contexts[0].pages:
            page = browser.contexts[0].pages[0]
        else:
            ctx = browser.contexts[0] if browser.contexts else browser.new_context(
                viewport={"width": 1365, "height": 850},
                locale="en-US",
                timezone_id="America/Costa_Rica",
            )
            page = ctx.new_page()
        page.set_default_timeout(30000)
        log("Connected.")

        session_results = []
        captcha_hit = False

        for i, target in enumerate(batch):
            name = target["business_name"]
            lat_hint = target.get("latitude", "")
            lon_hint = target.get("longitude", "")

            log(f"[{i + 1}/{len(batch)}] {name[:60]}")

            result = search_and_resolve(page, name)
            result["target_group"] = target.get("source", "unknown")
            session_results.append(result)

            # Save checkpoint immediately
            if result["success"]:
                done_set.add(name)
            done_set.add(name)  # Mark as attempted even on failure (don't retry in same session)
            checkpoint["done"] = list(done_set)
            checkpoint["session_count"] = session_num
            checkpoint["last_run"] = datetime.now().isoformat()
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2)

            # Append to results JSONL
            with open(RESULTS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

            # Status
            if result["cid"]:
                log(f"  CID: {result['cid']}  @{result['latitude']},{result['longitude']}  [{result['confidence']}]")
            elif result["maps_url"]:
                log(f"  Maps URL found  [{result['confidence']}]")
            else:
                log(f"  {result.get('error', 'Not found')}")

            # Check for CAPTCHA
            if result.get("error") and "CAPTCHA" in result["error"]:
                captcha_hit = True
                break

            # Delay between searches
            if i < len(batch) - 1 and not captcha_hit:
                delay = random.randint(MIN_DELAY, MAX_DELAY)
                log(f"  Waiting {delay}s...")
                time.sleep(delay)

        # Session summary
        success = sum(1 for r in session_results if r["success"])
        with_cid = sum(1 for r in session_results if r["cid"])
        log(f"\n--- Session {session_num} complete ---")
        log(f"Attempted: {len(session_results)}")
        log(f"Successful: {success}")
        log(f"With CID:   {with_cid}")
        if captcha_hit:
            log("⚠️  CAPTCHA hit — session stopped early")
            log(f"Recommend waiting 12-24h before next session")
        else:
            log(f"Session complete. Rest {REST_MINUTES} min before next.")
            log(f"Remaining: {len(remaining) - len(batch)}")

    finally:
        p.stop()
        chrome_proc.terminate()
        log("Chrome closed.")


if __name__ == "__main__":
    while True:
        main()
        # Check if done
        try:
            with open(CHECKPOINT_FILE) as f:
                cp = json.load(f)
            with open(TARGETS, encoding="utf-8-sig", newline="") as f:
                all_names = [r["business_name"] for r in csv.DictReader(f) if r.get("business_name")]
            remaining = [n for n in all_names if n not in cp.get("done", [])]
            if not remaining:
                log("All targets complete!")
                break
            mins = cp.get("rest_minutes", REST_MINUTES)
            log(f"Sleeping {mins} min before next session ({len(remaining)} remaining)...")
            time.sleep(mins * 60)
        except:
            break
