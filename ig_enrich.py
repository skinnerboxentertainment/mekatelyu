"""
Instagram enrichment: discover Instagram handles for businesses missing them.

Strategies in order:
1. Crawl real business websites for Instagram links
2. Fetch Google Maps pages (via CID) for Instagram links
"""

import csv
import json
import re
import time
import urllib.request
import urllib.parse
from collections import defaultdict

INPUT_CSV = "pv_within_5km.csv"
OUTPUT_CSV = "pv_within_5km_enriched.csv"
LOG_FILE = "ig_enrich_log.json"


def is_affiliate_link(url: str) -> bool:
    """Check if a URL is an affiliate/tracking link."""
    domains = [
        "anrdoezrs.net", "jdoqocy.com", "tkqlhce.com", "kqzyfj.com",
        "dpbolvw.net", "commissionjunction.com", "awltovhc.com",
        "shareasale.com", "vrbo.com/affiliate",
    ]
    return any(d in url.lower() for d in domains)


def extract_instagram_from_html(html: str, base_url: str = "") -> str | None:
    """Find the first instagram.com link in HTML."""
    # Direct instagram.com URLs
    for m in re.finditer(r'instagram\.com/([a-zA-Z0-9_.]+)', html):
        handle = m.group(1)
        # Skip common non-business patterns
        if handle.lower() in ("", "p", "explore", "accounts", "oauth", "developer", "about", "download"):
            continue
        return handle

    # Meta tags with instagram URLs
    for m in re.finditer(r'<meta\s+[^>]*content="([^"]*instagram[^"]+)"', html, re.I):
        url = m.group(1)
        h = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', url)
        if h:
            return h.group(1)

    return None


def fetch_url(url: str, timeout: int = 15) -> str | None:
    """Fetch a URL with basic headers, return text or None."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        resp = urllib.request.urlopen(req, timeout=timeout)
        # Only process text/html responses
        ctype = resp.headers.get("Content-Type", "")
        if "text/html" in ctype or "text/plain" in ctype:
            return resp.read().decode("utf-8", errors="replace")
        return None
    except Exception:
        return None


def extract_instagram_from_fb_url(fb_url: str) -> str | None:
    """
    Try to find Instagram from a Facebook page URL.
    We can't easily scrape Facebook (requires login).
    But we can check if the URL itself gives hints.
    This is a low-effort attempt.
    """
    return None


def main():
    # Load data
    with open(INPUT_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    print(f"Loaded {len(rows)} records", flush=True)

    # Add enrichment columns if not present
    enrichment_cols = [
        "instagram_enrich_source",
        "instagram_enrich_date",
        "instagram_enrich_confidence",
    ]
    for col in enrichment_cols:
        if col not in fieldnames:
            fieldnames.append(col)
    for r in rows:
        for col in enrichment_cols:
            if col not in r:
                r[col] = ""

    # Enrichment log
    log = []
    now = time.strftime("%Y-%m-%d")

    # ---- Strategy 1: Crawl real business websites ----
    strategy1_found = 0
    website_candidates = [r for r in rows
                          if not r.get("instagram_handle")
                          and r.get("website")
                          and not is_affiliate_link(r["website"])]

    print(f"\nStrategy 1: Crawling {len(website_candidates)} real business websites...", flush=True)

    for r in website_candidates:
        url = r["website"].strip()
        print(f"  Fetching: {url}", flush=True)
        html = fetch_url(url)
        if html:
            handle = extract_instagram_from_html(html, url)
            if handle:
                r["instagram_handle"] = handle
                r["instagram_url"] = f"https://www.instagram.com/{handle}/"
                r["instagram_enrich_source"] = "website_crawl"
                r["instagram_enrich_date"] = now
                r["instagram_enrich_confidence"] = "high"
                strategy1_found += 1
                log.append({
                    "strategy": "website_crawl",
                    "business": r.get("business_name"),
                    "url": url,
                    "found": handle,
                })
                print(f"    FOUND: {handle}", flush=True)
        time.sleep(1.0)

    print(f"  Strategy 1 found: {strategy1_found}", flush=True)

    # ---- Strategy 2: Fetch Google Maps pages via CID ----
    strategy2_found = 0
    cid_candidates = [r for r in rows
                      if not r.get("instagram_handle")
                      and r.get("google_maps_cid")
                      and not r.get("instagram_enrich_source")]

    print(f"\nStrategy 2: Checking {len(cid_candidates)} Google Maps CIDs...", flush=True)

    for r in cid_candidates:
        cid = r["google_maps_cid"].strip()
        maps_url = f"https://maps.google.com/?cid={cid}"
        print(f"  Fetching Maps page: cid={cid}", flush=True)
        html = fetch_url(maps_url, timeout=20)
        if html:
            # Look for Instagram in the page
            handle = extract_instagram_from_html(html)
            if handle:
                r["instagram_handle"] = handle
                r["instagram_url"] = f"https://www.instagram.com/{handle}/"
                r["instagram_enrich_source"] = "maps_cid"
                r["instagram_enrich_date"] = now
                r["instagram_enrich_confidence"] = "high"
                strategy2_found += 1
                log.append({
                    "strategy": "maps_cid",
                    "business": r.get("business_name"),
                    "cid": cid,
                    "found": handle,
                })
                print(f"    FOUND: {handle}", flush=True)
        time.sleep(1.5)  # Polite delay for Google

    print(f"  Strategy 2 found: {strategy2_found}", flush=True)

    # ---- Summary ----
    total_new = strategy1_found + strategy2_found
    final_with_ig = sum(1 for r in rows if r.get("instagram_handle"))
    print(f"\n{'='*50}", flush=True)
    print(f"ENRICHMENT RESULTS", flush=True)
    print(f"{'='*50}", flush=True)
    print(f"  New Instagram found:            {total_new}", flush=True)
    print(f"  Final with Instagram:           {final_with_ig} ({final_with_ig/len(rows)*100:.1f}%)", flush=True)
    print(f"  Still without Instagram:        {len(rows) - final_with_ig}", flush=True)

    # Write enriched CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Written: {OUTPUT_CSV}", flush=True)

    # Write log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"Log: {LOG_FILE}", flush=True)


if __name__ == "__main__":
    main()
