"""
Post-mortem: what a single Maps CID page contains vs what we extracted.
"""
import asyncio, json, re, sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)

CID = "9649993079907777710"
NAME = "Black Bamboo"


async def main():
    url = f"https://www.google.com/maps?cid={CID}"
    print(f"=== Deep CID Inspection: {NAME} ({CID}) ===")
    print(f"URL: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900}, locale="en-US")
        page = await context.new_page()

        await page.goto(url, wait_until="commit", timeout=30000)
        await page.wait_for_timeout(5000)

        # Handle cookie consent
        try:
            btn = await page.query_selector('button:has-text("Accept all")')
            if btn:
                await btn.click()
                await page.wait_for_timeout(2000)
        except:
            pass

        await page.wait_for_timeout(2000)

        # EXTRACT 1: Full visible text (not truncated)
        full_text = await page.evaluate("""
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

        # EXTRACT 2: JSON-LD structured data
        jsonld = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                return Array.from(scripts).map(s => s.textContent);
            }
        """)

        # EXTRACT 3: Meta tags
        metas = await page.evaluate("""
            () => {
                const tags = document.querySelectorAll('meta');
                return Array.from(tags).map(m => ({ name: m.getAttribute('name') || m.getAttribute('property'), content: m.getAttribute('content') }));
            }
        """)

        # EXTRACT 4: All visible HTML structure (first 5000 chars)
        body_html = await page.evaluate("""
            () => {
                const main = document.querySelector('[role="main"], #main, main') || document.body;
                return main.innerHTML.substring(0, 5000);
            }
        """)

        await browser.close()

    # Analyze what we have
    lines = full_text.split("\n")
    print(f"1. FULL VISIBLE TEXT: {len(full_text)} chars, {len(lines)} lines\n")

    # What data categories can we identify?
    data_types = {}

    # Business name - first substantive line
    biz_line = ""
    for l in lines:
        l = l.strip()
        if l and l not in ["Arrastra para cambiar.", "Arrastra para cambiar, haz clic para eliminar.", "Obtener app", "Ver fotos"] and len(l) > 3:
            biz_line = l
            break
    data_types["business_name"] = biz_line or "Not found"

    # Rating
    for l in lines:
        if re.match(r"^\d\.\d$", l.strip()):
            data_types["rating"] = float(l.strip())
            break

    # Subcategory (line after rating)
    for i, l in enumerate(lines):
        if re.match(r"^\d\.\d$", l.strip()):
            for j in range(i+1, min(i+5, len(lines))):
                nxt = lines[j].strip()
                if nxt and not re.match(r"^\d\.\d$", nxt) and len(nxt) > 2 and len(nxt) < 60:
                    data_types["subcategory"] = nxt
                    break
            break

    # Phone
    for l in lines:
        phone = re.search(r"(\+506\s*\d{4}\s*\d{4})|(\d{4}\s*\d{4})", l)
        if phone and "CRC" not in l and len(l) < 30:
            data_types["phone"] = phone.group(0).strip()
            break

    # Website
    for l in lines:
        if re.match(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}$", l, re.IGNORECASE) and "google" not in l.lower():
            data_types["website"] = l
            break

    # Address patterns
    for l in lines:
        if re.match(r"[A-Z]\d{3,}", l):
            data_types["plus_code"] = l
            break

    # Check-in / out
    ci = re.search(r"entrada[:\s]+([\d:.ap\s]+)", full_text, re.IGNORECASE)
    co = re.search(r"salida[:\s]+([\d:.ap\s]+)", full_text, re.IGNORECASE)
    if ci: data_types["check_in"] = ci.group(1).strip()
    if co: data_types["check_out"] = co.group(1).strip()

    # Amenities
    amenity_patterns = [
        r"Wi-Fi\s*(gratis)?",
        r"Estacionamiento\s*(gratuito)?",
        r"Piscina",
        r"Aire acondicionado",
        r"Restaurante",
        r"Gimnasio",
        r"Desayuno",
        r"Transporte",
        r"Admite",
        r"Mascotas",
        r"Acceso a la playa",
    ]
    amenities = set()
    for l in lines:
        for pat in amenity_patterns:
            if re.search(pat, l, re.IGNORECASE) and len(l) < 80:
                amenities.add(l.strip())
    if amenities:
        data_types["amenities"] = sorted(list(amenities))

    # Prices
    prices = [l.strip() for l in lines if re.search(r"CRC\s*[\d,]+", l)]
    if prices:
        data_types["prices"] = prices[:5]

    # Review count
    for l in lines:
        rc = re.search(r"\((\d+)\)", l)
        if rc and "CRC" not in l and len(l) < 20:
            maybe_count = int(rc.group(1))
            if maybe_count > 20:  # likely a review count, not a coordinate
                data_types["review_count"] = maybe_count
                break

    # Hours of operation
    hour_lines = [l.strip() for l in lines if re.match(r"\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?\s*[-–to]\s*\d{1,2}:\d{2}\s*[ap]\.?\s*m\.?", l, re.IGNORECASE)]
    if hour_lines:
        data_types["hours"] = hour_lines[:7]

    # Nearby business names
    nearby = [l.strip() for l in lines if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,5}$", l) and len(l) > 10 and "CRC" not in l and l not in ["Obtener app", "Ver fotos", "Indicaciones", "Guardar", "Cerca", "Compartir"]]
    if nearby:
        data_types["nearby_businesses"] = nearby[:5]

    # Write to file to avoid encoding issues
    out_path = Path("docs/paradisio_app/screenshots") / f"cid_postmortem_{CID}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Deep CID Inspection: {NAME} ({CID})\n{'='*60}\n\n")
        f.write(f"1. FULL VISIBLE TEXT: {len(full_text)} chars, {len(lines)} lines\n\n")
        for k, v in data_types.items():
            if isinstance(v, list):
                f.write(f"  {k}:\n")
                for item in v:
                    f.write(f"    - {item}\n")
            else:
                f.write(f"  {k}: {v}\n")

        f.write(f"\n\n2. JSON-LD STRUCTURED DATA: {len(jsonld)} blocks\n")
        for i, jd in enumerate(jsonld):
            f.write(f"\n  Block {i}:\n")
            try:
                parsed = json.loads(jd)
                f.write(json.dumps(parsed, indent=2)[:2000])
            except:
                f.write(f"(parse error, {len(jd)} chars)\n")
                f.write(jd[:500])

        f.write(f"\n\n3. META TAGS: {len(metas)} found\n")
        for m in metas[:15]:
            if m.get("name") or m.get("content"):
                f.write(f"  {m.get('name','') or m.get('property','')}: {m.get('content','')[:100]}\n")

        f.write(f"\n\n4. VISIBLE HTML (first 1000 chars):\n")
        f.write(body_html[:1000])

        f.write(f"\n\n=== SUMMARY ===\n")
        captured = [k for k in data_types.keys() if k != "business_name"]
        f.write(f"\nCAPTURED ({len(captured)} fields):\n")
        for c in captured:
            f.write(f"  - {c}\n")

        available = [
            "review_count / ratings count",
            "hours_of_operation (daily open/close times)",
            "photo URLs and image references",
            "business description text (from Maps)",
            "price_level ($/$$/$$$)",
            "popular times",
            "menu links (restaurants)",
            "delivery / takeout ordering links",
            "social media links from profile",
            "business attributes (outdoor seating, vegan options, etc.)",
            "full HTML DOM structure",
            "JSON-LD / structured data",
            "review snippets / user reviews",
            "latitude/longitude alternate sources",
        ]
        # Check which we actually already have
        already_have = set(captured)
        truly_missing = [a for a in available if not any(k in a.lower() for k in already_have)]
        f.write(f"\nAVAILABLE ON MAPS PAGE BUT NOT EXTRACTED ({len(truly_missing)} fields):\n")
        for a in truly_missing:
            f.write(f"  - {a}\n")

        # Also show all raw lines for reference
        f.write(f"\n\n5. ALL VISIBLE TEXT LINES (raw):\n")
        for i, l in enumerate(lines):
            f.write(f"  [{i:3d}] {l}\n")

    print(f"Written to {out_path}")
    print(f"Summary: {len(captured)} fields captured, {len(truly_missing)} fields available but not extracted")


if __name__ == "__main__":
    asyncio.run(main())
