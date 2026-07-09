"""
v2 CID batch scrape on 11 representative businesses.
Captures full text, links, images for post-hoc analysis.
"""
import asyncio, json, sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)

SAMPLE = [
    {"slug": "black-bamboo-puerto-viejo", "name": "Black Bamboo", "cid": "9649993079907777710", "category": "hotel"},
    {"slug": "rocking-j-s-hostel-puerto-viejo", "name": "Rocking J's Hostel", "cid": "18217868124175231590", "category": "hostel"},
    {"slug": "la-tica-y-la-gata-puerto-viejo", "name": "La Tica y La Gata", "cid": "11047054352277007542", "category": "hotel"},
    {"slug": "gigi-o-restaurant-puerto-viejo", "name": "Gigi O Restaurant", "cid": "4732141069441829785", "category": "restaurant"},
    {"slug": "tasty-waves-cantina-playa-cocles-puerto-viejo-lim-n-costa-rica-cocles", "name": "Tasty Waves Cantina", "cid": "10844386752467925201", "category": "restaurant"},
    {"slug": "pizzeria-pulcinella-playa-chiquita-puerto-viejo-lim-n-costa-rica-playa-chiquita", "name": "Pizzeria Pulcinella", "cid": "16086292581675314185", "category": "restaurant"},
    {"slug": "old-harbour-supermarket-puerto-viejo", "name": "Old Harbour Supermarket", "cid": "15754056459834286605", "category": "shopping"},
    {"slug": "tienda-caribe-puerto-viejo", "name": "Tienda Caribe", "cid": "11658160512809789635", "category": "shopping"},
    {"slug": "jaguar-rescue-center-playa-chiquita-puerto-viejo-lim-n-costa-rica-playa-chiquita", "name": "Jaguar Rescue Center", "cid": "9435208628058025334", "category": "tour_company"},
    {"slug": "black-shack-surf-school-playa-cocles-puerto-viejo-lim-n-costa-rica-cocles", "name": "Black Shack Surf School", "cid": "2735238038335804141", "category": "services"},
    {"slug": "lavander-a-la-estrella-puerto-viejo", "name": "Lavanderia La Estrella", "cid": "1889608973525699671", "category": "services"},
]

OUT_DIR = Path("docs/paradisio_app/data/cid_v2_samples")
OUT_DIR.mkdir(parents=True, exist_ok=True)


async def scrape_one(browser, biz):
    url = f"https://www.google.com/maps?cid={biz['cid']}"
    context = await browser.new_context(viewport={"width": 1400, "height": 900}, locale="en-US")
    page = await context.new_page()
    result = {
        "slug": biz["slug"], "name": biz["name"], "cid": biz["cid"],
        "category": biz["category"], "url": url,
        "success": False, "error": None,
        "visible_text": "", "text_length": 0,
        "links": [], "images": [], "jsonld": [], "page_title": "",
    }
    try:
        await page.goto(url, wait_until="commit", timeout=30000)
        await page.wait_for_timeout(5000)
        try:
            btn = await page.query_selector('button:has-text("Accept all")')
            if btn:
                await btn.click()
                await page.wait_for_timeout(2000)
        except:
            pass
        await page.wait_for_timeout(2000)
        result["page_title"] = await page.title()
        result["visible_text"] = await page.evaluate("""
            () => {
                const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                let t = [];
                let n;
                while (n = w.nextNode()) {
                    const s = n.textContent.trim();
                    if (s.length > 1) {
                        const st = window.getComputedStyle(n.parentElement);
                        if (st.display !== 'none' && st.visibility !== 'hidden') t.push(s);
                    }
                }
                return t.join('\\n');
            }
        """)
        result["text_length"] = len(result["visible_text"])
        result["links"] = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: (a.innerText||'').trim().slice(0,100), href: a.href
            })).filter(l => l.text && l.href && !l.href.startsWith('javascript:'));
        """)
        result["images"] = await page.evaluate("""
            () => Array.from(document.querySelectorAll('img[src]')).map(i => ({
                alt: i.alt.slice(0,80), src: i.src
            })).filter(i => !i.src.includes('google.com/maps/vt/pb'));
        """)
        result["jsonld"] = await page.evaluate("""
            () => Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s => s.textContent);
        """)
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)[:200]
    finally:
        await context.close()
    return result


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        results = []
        for i, biz in enumerate(SAMPLE):
            print(f"  [{i+1}/{len(SAMPLE)}] {biz['name']} ({biz['category']})...")
            result = await scrape_one(browser, biz)
            results.append(result)
            status = "OK" if result["success"] else f"FAIL ({result['error']})"
            print(f"    {status} — {result['text_length']} chars, {len(result['links'])} links, {len(result['images'])} images")
        await browser.close()
    with open(OUT_DIR / "batch_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nDone. Results saved to {OUT_DIR / 'batch_results.json'}")


if __name__ == "__main__":
    asyncio.run(main())
