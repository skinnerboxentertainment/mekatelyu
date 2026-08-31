"""
Batch Maps CID enricher. Crawls all 699 CIDs with pacing, extracts ratings, address,
phone, website, hours, amenities, and competitor intelligence.
Resumable — run, stop, run again.
"""

import asyncio
import json
import re
import sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)

BUSINESSES_JSON = Path(__file__).resolve().parent.parent / "docs" / "paradisio_app" / "data" / "businesses.json"
RESULTS_PATH = Path(__file__).resolve().parent.parent / "docs" / "paradisio_app" / "data" / "maps_enrich.json"
CHECKPOINT_PATH = Path(__file__).resolve().parent.parent / "docs" / "paradisio_app" / "data" / "maps_checkpoint.json"

BATCH_SIZE = 20       # CIDs between breaks
BREAK_SECS = 60       # long break after batch
MIN_DELAY = 8         # min seconds between requests
MAX_DELAY = 15        # max seconds between requests
MAX_RETRIES = 2       # retries on failure per CID
CID_TIMEOUT = 30      # seconds per CID page load

MONTHS_ES = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12}


def load_businesses():
    with open(BUSINESSES_JSON) as f:
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
    print(f"\nSaved {len(results)} results to {RESULTS_PATH}")


def parse_maps_text(text, biz_name):
    """Parse visible text from Maps page into structured fields."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    result = {
        "rating": None,
        "phone": None,
        "website": None,
        "address": None,
        "check_in": None,
        "check_out": None,
        "amenities": [],
        "prices": [],
        "nearby": [],
    }

    for i, line in enumerate(lines):
        # Rating: standalone number like "4.7" near the business name
        if re.match(r"^\d\.\d$", line) and result["rating"] is None:
            result["rating"] = float(line)

        # Phone: Costa Rica numbers
        phone = re.search(r"(\+506\s*\d{4}\s*\d{4})|(\d{4}\s*\d{3}\s*\d{3})|(\d{4}\s*\d{4})", line)
        if phone and result["phone"] is None:
            result["phone"] = phone.group(0).strip()

        # Website hostname-like string (not google.com, not CRC prices)
        if re.match(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}$", line, re.IGNORECASE) and "google" not in line:
            if result["website"] is None:
                result["website"] = line

        # Address: "M742+8M" pattern or coordinates
        if re.match(r"[A-Z]\d{3,}", line) and result["address"] is None:
            result["address"] = line

        # Check-in / Check-out
        entrada = re.search(r"entrada[:\s]+([\d:.\s]+[ap]\.?\s*m\.?)", line, re.IGNORECASE)
        if entrada and result["check_in"] is None:
            result["check_in"] = entrada.group(1).strip()
        salida = re.search(r"salida[:\s]+([\d:.\s]+[ap]\.?\s*m\.?)", line, re.IGNORECASE)
        if salida and result["check_out"] is None:
            result["check_out"] = salida.group(1).strip()

        # Amenities: "Wi-Fi gratis", "Estacionamiento gratuito", etc.
        amenity = re.match(r"^(Wi-Fi|Estacionamiento|Piscina|Aire acondicionado|Restaurante|Gimnasio|Desayuno|Transporte|Admite|Mascotas|Acceso)", line, re.IGNORECASE)
        if amenity:
            result["amenities"].append(line)

        # Prices: "CRC 51,422"
        price = re.search(r"CRC\s*[\d,]+", line)
        if price:
            result["prices"].append(line)

    return result


async def extract_cid(browser, cid, biz_name):
    """Extract data from a single Maps CID."""
    url = f"https://www.google.com/maps?cid={cid}"
    context = await browser.new_context(
        viewport={"width": 1400, "height": 900},
        locale="en-US",
    )
    page = await context.new_page()
    result = {"cid": cid, "business": biz_name, "success": False, "data": None, "error": None}

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

        # Wait for content
        try:
            await page.wait_for_selector("h1, [role=main]", timeout=10000)
        except Exception:
            pass
        await page.wait_for_timeout(2000)

        # Extract visible text
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

        parsed = parse_maps_text(text, biz_name)
        result["data"] = parsed
        result["text_sample"] = text[:300]
        result["text_length"] = len(text)
        result["success"] = True

    except Exception as e:
        result["error"] = str(e)[:200]

    finally:
        await context.close()

    return result


async def main():
    businesses = load_businesses()
    with_cids = [b for b in businesses if b["channels"]["google_maps_cid"]]
    total = len(with_cids)
    print(f"Total businesses: {len(businesses)}, with CIDs: {total}")

    checkpoint = load_checkpoint()
    completed = set(checkpoint["completed"])
    results = checkpoint["results"]
    remaining = [b for b in with_cids if b["channels"]["google_maps_cid"] not in completed]

    if not remaining:
        print("All CIDs already processed.")
        return

    print(f"Already done: {len(completed)}, Remaining: {len(remaining)}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        batch_count = 0
        total_done = len(completed)

        for idx, biz in enumerate(remaining):
            cid = biz["channels"]["google_maps_cid"]
            name = biz["name"]

            for attempt in range(MAX_RETRIES + 1):
                result = await extract_cid(browser, cid, name)
                if result["success"]:
                    break
                print(f"  Retry {attempt + 1}/{MAX_RETRIES} for {name}")
                await asyncio.sleep(3)

            results.append(result)
            completed.add(cid)
            total_done += 1

            status = "OK" if result["success"] else f"FAIL ({result['error']})"
            rating = result["data"]["rating"] if result["success"] and result["data"] else "-"
            print(f"  [{total_done}/{total}] {name[:40]:40s} rating={rating}  {status}")

            # Save checkpoint every batch
            if total_done % BATCH_SIZE == 0:
                save_checkpoint({"completed": list(completed), "results": results})
                save_final(results)
                print(f"  --- Batch done. Taking {BREAK_SECS}s break ---")
                await asyncio.sleep(BREAK_SECS)
            else:
                delay = MIN_DELAY + (hash(cid) % (MAX_DELAY - MIN_DELAY + 1))
                await asyncio.sleep(delay)

        await browser.close()

    save_checkpoint({"completed": list(completed), "results": results})
    save_final(results)

    # Summary
    succeeded = sum(1 for r in results if r["success"])
    rated = sum(1 for r in results if r["success"] and r["data"] and r["data"]["rating"])
    print(f"\nDone. Total: {len(results)}, Success: {succeeded}, With ratings: {rated}")


if __name__ == "__main__":
    asyncio.run(main())
