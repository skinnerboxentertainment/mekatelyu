"""
v2 Batch Maps CID enricher — authenticated Chrome via CDP.
Connects to your signed-in Chrome. Saves full text per CID.
Resumable — kill it anytime, re-run to continue.
"""
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)

BASE = Path(__file__).resolve().parent.parent
BUSINESSES_JSON = BASE / "docs" / "paradisio_app" / "data" / "businesses.json"
RESULTS_PATH = BASE / "docs" / "paradisio_app" / "data" / "maps_enrich_v2.json"
CHECKPOINT_PATH = BASE / "docs" / "paradisio_app" / "data" / "maps_checkpoint_v2.json"
LOG_FILE = BASE / "maps_enrich_v2.log"

CDP_PORT = 9222

BATCH_SIZE = 20
BREAK_SECS = 60
MIN_DELAY = 8
MAX_DELAY = 15
MAX_RETRIES = 2
CID_TIMEOUT = 30


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        print(line, flush=True)
    except:
        pass
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()


def load_businesses():
    with open(BUSINESSES_JSON, encoding="utf-8") as f:
        return json.load(f)


def load_checkpoint():
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"completed": [], "results": []}


def save_checkpoint(data):
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_final(results):
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    log(f"Saved {len(results)} results to {RESULTS_PATH.name}")


def parse_maps_text(text):
    """Parse visible text from Maps page into structured fields."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    result = {
        "rating": None,
        "phone": None,
        "website": None,
        "address": None,
        "check_in": None,
        "check_out": None,
        "open_status": None,
        "hours": None,
        "amenities": [],
        "prices": [],
    }

    for i, line in enumerate(lines):
        if re.match(r"^\d\.\d$", line) and result["rating"] is None:
            result["rating"] = float(line)

        phone = re.search(r"(\+506\s*\d{4}\s*\d{4})|(\d{4}\s*\d{3}\s*\d{3})|(\d{4}\s*\d{4})", line)
        if phone and result["phone"] is None:
            result["phone"] = phone.group(0).strip()

        if re.match(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}$", line, re.IGNORECASE) and "google" not in line:
            if result["website"] is None:
                result["website"] = line

        if re.match(r"[A-Z]\d{3,}", line) and result["address"] is None:
            result["address"] = line

        entrada = re.search(r"entrada[:\s]+([\d:.\s]+[ap]\.?\s*m\.?)", line, re.IGNORECASE)
        if entrada and result["check_in"] is None:
            result["check_in"] = entrada.group(1).strip()
        salida = re.search(r"salida[:\s]+([\d:.\s]+[ap]\.?\s*m\.?)", line, re.IGNORECASE)
        if salida and result["check_out"] is None:
            result["check_out"] = salida.group(1).strip()

        if re.search(r"\b(abierto|cerrado|open|closed)\b", line, re.IGNORECASE):
            if result["open_status"] is None:
                result["open_status"] = line.strip()

        if re.search(r"\d{1,2}:\d{2}\s*(a\.?m\.?|p\.?m\.?)", line, re.IGNORECASE):
            if result["hours"] is None:
                result["hours"] = line.strip()

        amenity = re.match(
            r"^(Wi-Fi|Estacionamiento|Piscina|Aire acondicionado|Restaurante|"
            r"Gimnasio|Desayuno|Transporte|Admite|Mascotas|Acceso|Parking|"
            r"Wifi|Pool|Air conditioning|Breakfast)",
            line, re.IGNORECASE
        )
        if amenity:
            result["amenities"].append(line)

        price = re.search(r"CRC\s*[\d,]+", line)
        if price:
            result["prices"].append(line)

    return result


async def extract_cid(page, cid, biz_name):
    """Extract data from a single Maps CID using authenticated page."""
    url = f"https://www.google.com/maps?cid={cid}"
    result = {
        "cid": cid,
        "business": biz_name,
        "success": False,
        "data": None,
        "full_text": "",
        "text_length": 0,
        "error": None,
    }

    try:
        await page.goto(url, wait_until="commit", timeout=CID_TIMEOUT * 1000)
        await page.wait_for_timeout(4000)

        # Dismiss cookie/consent dialogs
        try:
            for btn_text in ["Accept all", "Reject all", "Aceptar", "Rechazar"]:
                btn = await page.query_selector(f'button:has-text("{btn_text}")')
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(1500)
                    break
        except Exception:
            pass

        try:
            await page.wait_for_selector("h1, [role=main]", timeout=10000)
        except Exception:
            pass
        await page.wait_for_timeout(2000)

        # Save FULL visible text (v2: capture-then-parse)
        text = await page.evaluate("""
            () => {
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null, false
                );
                let texts = [];
                let node;
                while (node = walker.nextNode()) {
                    const t = node.textContent.trim();
                    if (t.length > 1) {
                        const style = window.getComputedStyle(node.parentElement);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            texts.push(t);
                        }
                    }
                }
                return texts.join('\\n');
            }
        """)

        parsed = parse_maps_text(text)
        result["data"] = parsed
        result["full_text"] = text
        result["text_length"] = len(text)
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)[:200]

    return result


async def main():
    print("=" * 60)
    print("MAPS ENRICHMENT v2 — authenticated Chrome via CDP")
    print("=" * 60)

    businesses = load_businesses()
    with_cids = [b for b in businesses if b["channels"]["google_maps_cid"]]
    total = len(with_cids)
    log(f"Total businesses: {len(businesses)}, with CIDs: {total}")

    checkpoint = load_checkpoint()
    completed = set(checkpoint["completed"])
    results = checkpoint["results"]

    # Only include CIDs that still exist in the current dataset
    valid_cids = {b["channels"]["google_maps_cid"] for b in with_cids}
    completed = completed & valid_cids
    remaining = [b for b in with_cids if b["channels"]["google_maps_cid"] not in completed]

    if not remaining:
        log("All CIDs already processed!")
        return

    log(f"Already done: {len(completed)}, Remaining: {len(remaining)}")

    # Connect to your signed-in Chrome
    log(f"Connecting to Chrome on CDP port {CDP_PORT}...")
    p = async_playwright()
    p_obj = await p.start()
    ctx = None
    try:
        browser = await p_obj.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        ctx = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="en-US",
        )
        page = await ctx.new_page()
        page.set_default_timeout(CID_TIMEOUT * 1000)
        log("Connected.\n")

        batch_count = 0
        total_done = len(completed)

        for idx, biz in enumerate(remaining):
            cid = biz["channels"]["google_maps_cid"]
            name = biz["name"]

            for attempt in range(MAX_RETRIES + 1):
                result = await extract_cid(page, cid, name)
                if result["success"]:
                    break
                log(f"  Retry {attempt + 1}/{MAX_RETRIES} for {name}")
                await asyncio.sleep(3)

            results.append(result)
            completed.add(cid)
            total_done += 1

            status = "OK" if result["success"] else "FAIL"
            rating = result["data"]["rating"] if result["success"] and result["data"] else "-"
            tl = result["text_length"] if result["success"] else 0
            log(f"  [{total_done}/{total}] {name[:40]:40s} rating={rating}  text={tl}  {status}")

            # Save checkpoint
            save_checkpoint({"completed": list(completed), "results": results})

            # Break or delay
            if total_done % BATCH_SIZE == 0:
                save_final(results)
                log(f"  --- Batch done ({total_done}/{total}). Taking {BREAK_SECS}s break ---")
                await asyncio.sleep(BREAK_SECS)
            else:
                delay = MIN_DELAY + (hash(cid) % (MAX_DELAY - MIN_DELAY + 1))
                await asyncio.sleep(delay)

        await ctx.close()

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        log(traceback.format_exc()[-500:])
    finally:
        try:
            await ctx.close()
        except:
            pass
        await p_obj.stop()
        log("Disconnected from Chrome. Your browser stays open.")

    save_checkpoint({"completed": list(completed), "results": results})
    save_final(results)

    succeeded = sum(1 for r in results if r["success"])
    rated = sum(1 for r in results if r["success"] and r["data"] and r["data"]["rating"])
    log(f"\nDone. Total: {len(results)}, Success: {succeeded}, With ratings: {rated}")


if __name__ == "__main__":
    asyncio.run(main())
