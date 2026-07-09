"""
Full deep scrape of a single CID — captures everything available.
"""
import asyncio, json, re, sys
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("pip install playwright && playwright install chromium")
    sys.exit(1)

CID = "8711730419987475064"
NAME = "Caribeans Coffee and Chocolate"


async def main():
    url = f"https://www.google.com/maps?cid={CID}"
    out_dir = Path("docs/paradisio_app/screenshots")
    out_dir.mkdir(parents=True, exist_ok=True)
    report = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900}, locale="en-US")
        page = await context.new_page()

        await page.goto(url, wait_until="commit", timeout=30000)
        await page.wait_for_timeout(5000)

        try:
            btn = await page.query_selector('button:has-text("Accept all")')
            if btn:
                await btn.click()
                await page.wait_for_timeout(2000)
        except:
            pass

        await page.wait_for_timeout(3000)

        # Screenshot
        await page.screenshot(path=str(out_dir / f"maps_deep_{CID}.png"), full_page=False)

        # Full visible text
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

        # All href links on the page
        links = await page.evaluate("""
            () => {
                const anchors = document.querySelectorAll('a[href]');
                return Array.from(anchors).map(a => ({ text: a.innerText.trim().slice(0, 80), href: a.href }));
            }
        """)

        # All images with their alt text
        images = await page.evaluate("""
            () => {
                const imgs = document.querySelectorAll('img[src]');
                return Array.from(imgs).map(i => ({ alt: i.alt, src: i.src }));
            }
        """)

        # JSON-LD
        jsonld = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                return Array.from(scripts).map(s => s.textContent);
            }
        """)

        # Meta tags
        metas = await page.evaluate("""
            () => {
                const tags = document.querySelectorAll('meta');
                return Array.from(tags).map(m => ({ name: m.getAttribute('name') || m.getAttribute('property') || '', content: (m.getAttribute('content') || '').slice(0, 200) }));
            }
        """)

        # Page title
        title = await page.title()

        await browser.close()

    # Write full report
    lines = full_text.split("\n")

    with open(out_dir / f"maps_deep_{CID}.txt", "w", encoding="utf-8") as f:
        f.write(f"DEEP CID SCRAPE: {NAME} (CID {CID})\n")
        f.write(f"URL: {url}\n")
        f.write(f"Title: {title}\n")
        f.write(f"{'='*60}\n\n")

        f.write(f"VISIBLE TEXT: {len(full_text)} chars, {len(lines)} lines\n")
        f.write(f"{'-'*60}\n")
        for i, l in enumerate(lines):
            f.write(f"  [{i:3d}] {l}\n")

        f.write(f"\n\nLINKS: {len(links)} found\n")
        f.write(f"{'-'*60}\n")
        for link in links:
            if link["text"] and not link["href"].startswith("javascript:"):
                f.write(f"  {link['text'][:60]:60s} {link['href'][:80]}\n")

        f.write(f"\n\nIMAGES: {len(images)} found\n")
        f.write(f"{'-'*60}\n")
        seen = set()
        for img in images:
            if img["src"] not in seen:
                seen.add(img["src"])
                alt = img["alt"][:60]
                src = img["src"][:100]
                if "google" in src or "maps" in src:
                    f.write(f"  [{alt:60s}] {src}\n")

        f.write(f"\n\nJSON-LD: {len(jsonld)} blocks\n")
        f.write(f"{'-'*60}\n")
        for i, jd in enumerate(jsonld):
            try:
                parsed = json.loads(jd)
                f.write(json.dumps(parsed, indent=2))
            except:
                f.write(f"(parse error, {len(jd)} chars)")

        f.write(f"\n\nMETA TAGS: {len(metas)}\n")
        f.write(f"{'-'*60}\n")
        for m in metas:
            if m["name"] or m["content"]:
                f.write(f"  {m['name']:25s} {m['content'][:120]}\n")

    print(f"Written: {out_dir / f'maps_deep_{CID}.txt'}")
    print(f"Screenshot: {out_dir / f'maps_deep_{CID}.png'}")
    print(f"Visible text: {len(full_text)} chars, {len(lines)} lines")
    print(f"Links: {len(links)}, Images: {len(images)}, JSON-LD: {len(jsonld)}")


if __name__ == "__main__":
    asyncio.run(main())
