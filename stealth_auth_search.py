"""
Authenticated stealth search — connects to YOUR signed-in Chrome via CDP.
Opens its own tab so you can browse freely. Never kills or relaunches Chrome.
Checkpoint-saved after each search — safe to Ctrl+C at any time.
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

from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent
SCREENSHOTS_DIR = BASE / "stealth_screenshots"
CHECKPOINT_FILE = BASE / "stealth_checkpoint.json"
RESULTS_FILE = BASE / "stealth_results.jsonl"
LOG_FILE = BASE / "stealth_session.log"
TARGETS = BASE / "stealth_targets.csv"

CDP_PORT = 9222

MIN_DELAY = 15
MAX_DELAY = 25
SESSION_MAX = 250
REST_MINUTES = 1


LOG_BUFFER = []
def log(msg, flush=False):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line, flush=True)
    except:
        pass
    LOG_BUFFER.append(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()


def extract_from_maps_url(url):
    result = {"cid": "", "lat": "", "lon": ""}
    m = re.search(r'!1s0x[a-f0-9]+:0x([a-f0-9]+)', url, re.I)
    if m:
        result["cid"] = str(int(m.group(1), 16))
    if not result["cid"]:
        m = re.search(r'[?&]cid=(\d{10,})', url)
        if m:
            result["cid"] = m.group(1)
    m = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', url)
    if m:
        result["lat"] = m.group(1)
        result["lon"] = m.group(2)
    if not result["lat"] or not result["lon"]:
        m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if m:
            result["lat"] = m.group(1)
            result["lon"] = m.group(2)
    return result


def detect_captcha(page):
    try:
        body = page.inner_text("body").lower()[:500]
        if "unusual traffic" in body or "captcha" in body or "sorry" in body:
            return True
    except:
        pass
    return False


PV_CENTER_LAT = 9.655
PV_CENTER_LON = -82.753
PV_RADIUS_DEG = 0.045


def in_pv_area(lat, lon):
    try:
        lat_f, lon_f = float(lat), float(lon)
        return (
            abs(lat_f - PV_CENTER_LAT) <= PV_RADIUS_DEG
            and abs(lon_f - PV_CENTER_LON) <= PV_RADIUS_DEG
        )
    except (ValueError, TypeError):
        return False


def search_and_resolve(page, name):
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
        time.sleep(random.uniform(5, 12))

        if detect_captcha(page):
            result["error"] = "CAPTCHA or unusual traffic detected"
            log(f"  CAPTCHA detected — stopping session")
            return result

        final_url = page.url

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

        extracted = extract_from_maps_url(final_url)
        result["maps_url"] = final_url.split("&")[0]
        result["cid"] = extracted["cid"]
        result["cid_source"] = "hex_feature_id" if extracted["cid"] and "!1s" in final_url else "url_param" if extracted["cid"] else ""
        result["latitude"] = extracted["lat"]
        result["longitude"] = extracted["lon"]

        try:
            tel = page.query_selector('a[href^="tel:"]')
            if tel:
                result["phone"] = (tel.get_attribute("href") or "").replace("tel:", "")
        except:
            pass

        try:
            web = page.query_selector('a[data-item-id="authority"], button:has-text("Website")')
            if web:
                result["website"] = web.get_attribute("href") or ""
        except:
            pass

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
    print("AUTHENTICATED STEALTH SEARCH (uses your signed-in Chrome)")
    print("=" * 60)

    checkpoint = {"done": [], "session_count": 0, "last_run": ""}
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, encoding="utf-8") as f:
                checkpoint = json.load(f)
            log(f"Loaded checkpoint: {len(checkpoint.get('done', []))} done, "
                f"{checkpoint.get('session_count', 0)} sessions")
        except:
            pass

    session_num = checkpoint.get("session_count", 0) + 1
    done_set = set(checkpoint.get("done", []))

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

    batch = remaining[:SESSION_MAX]
    log(f"This session: {len(batch)} searches")

    # Connect to YOUR already-running Chrome — no killing, no relaunching
    log(f"Connecting to Chrome on CDP port {CDP_PORT}...")
    p = sync_playwright().start()
    try:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")

        # Create a NEW context so we don't touch the user's tabs
        ctx = browser.new_context(
            viewport={"width": 1365, "height": 850},
            locale="en-US",
            timezone_id="America/Costa_Rica",
        )
        page = ctx.new_page()
        page.set_default_timeout(30000)
        log("Connected. Your browsing is unaffected — script uses its own tab.\n")

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

            if result["success"]:
                done_set.add(name)
            done_set.add(name)
            checkpoint["done"] = list(done_set)
            checkpoint["session_count"] = session_num
            checkpoint["last_run"] = datetime.now().isoformat()
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2)

            with open(RESULTS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

            if result["cid"]:
                log(f"  CID: {result['cid']}  @{result['latitude']},{result['longitude']}  [{result['confidence']}]")
            elif result["maps_url"]:
                log(f"  Maps URL found  [{result['confidence']}]")
            else:
                log(f"  {result.get('error', 'Not found')}")

            if result.get("error") and "CAPTCHA" in result["error"]:
                captcha_hit = True
                break

            if i < len(batch) - 1 and not captcha_hit:
                delay = random.randint(MIN_DELAY, MAX_DELAY)
                log(f"  Waiting {delay}s...")
                time.sleep(delay)

        success = sum(1 for r in session_results if r["success"])
        with_cid = sum(1 for r in session_results if r["cid"])
        log(f"\n--- Session {session_num} complete ---")
        log(f"Attempted: {len(session_results)}")
        log(f"Successful: {success}")
        log(f"With CID:   {with_cid}")
        if captcha_hit:
            log("CAPTCHA hit — session stopped early. Recommend waiting 12-24h.")
        else:
            log(f"Session complete. Rest {REST_MINUTES} min before next.")
            log(f"Remaining: {len(remaining) - len(batch)}")

    except Exception as e:
        log(f"SESSION ERROR: {e}")
        import traceback
        log(traceback.format_exc()[-500:])
    finally:
        try:
            ctx.close()
        except:
            pass
        p.stop()
        log("Disconnected from Chrome. Your Chrome window stays open.")


if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            log(f"FATAL: main() crashed: {e}")
            import traceback
            log(traceback.format_exc()[-500:])
        try:
            with open(CHECKPOINT_FILE) as f:
                cp = json.load(f)
            with open(TARGETS, encoding="utf-8-sig", newline="") as f:
                all_names = [r["business_name"] for r in csv.DictReader(f) if r.get("business_name")]
            remaining = [n for n in all_names if n not in cp.get("done", [])]
            if not remaining:
                log("All targets complete!")
                break
            mins = REST_MINUTES
            log(f"Sleeping {mins} min before next session ({len(remaining)} remaining)...")
            time.sleep(mins * 60)
        except Exception as e:
            log(f"FATAL: post-session check failed: {e}")
            time.sleep(60)
