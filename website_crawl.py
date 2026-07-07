"""
Visit 191 websites from the master dataset, extract social links:
Instagram, Facebook, WhatsApp, Booking.com, TikTok, YouTube, Twitter, email.
"""
import csv
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin

import httpx

BASE = Path(__file__).parent
LOG_FILE = BASE / "website_crawl_log.json"
RESULTS_FILE = BASE / "website_crawl_results.csv"

# Timeout per request
TIMEOUT = 15

# Social patterns (case-insensitive)
SOCIAL_PATTERNS = {
    "instagram_url": [
        r'(?:https?:)?//(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+/?',
    ],
    "facebook_url": [
        r'(?:https?:)?//(?:www\.)?facebook\.com/[a-zA-Z0-9.]+/?',
        r'(?:https?:)?//(?:www\.)?fb\.com/[a-zA-Z0-9.]+/?',
    ],
    "whatsapp": [
        r'(?:https?:)?//(?:api\.)?whatsapp\.com/send\?phone=(\d+)',
        r'(?:https?:)?//wa\.me/(\d+)',
    ],
    "booking_url": [
        r'(?:https?:)?//(?:www\.)?booking\.com/hotel/[a-z-]+\.html',
        r'(?:https?:)?//(?:www\.)?booking\.com/Share-[a-zA-Z0-9]+',
    ],
    "tiktok_url": [
        r'(?:https?:)?//(?:www\.)?tiktok\.com/@[a-zA-Z0-9_.]+',
    ],
    "youtube_url": [
        r'(?:https?:)?//(?:www\.)?youtube\.com/@[a-zA-Z0-9_.]+',
        r'(?:https?:)?//(?:www\.)?youtube\.com/channel/[a-zA-Z0-9_-]+',
        r'(?:https?:)?//(?:www\.)?youtube\.com/c/[a-zA-Z0-9_.]+',
    ],
    "twitter_url": [
        r'(?:https?:)?//(?:www\.)?twitter\.com/[a-zA-Z0-9_]+',
        r'(?:https?:)?//(?:www\.)?x\.com/[a-zA-Z0-9_]+',
    ],
    "email": [
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ],
}

def extract_social(html, base_url):
    """Extract all social links from HTML content."""
    found = {}
    for field, patterns in SOCIAL_PATTERNS.items():
        matches = set()
        for pat in patterns:
            for m in re.finditer(pat, html, re.I):
                url = m.group(0)
                if not url.startswith("http"):
                    url = "https:" + url
                # Normalize
                url = url.rstrip("/")
                matches.add(url)
        if matches:
            found[field] = sorted(matches)
    return found


def crawl_website(url):
    """Fetch a website and extract social links."""
    result = {
        "url": url,
        "status": 0,
        "error": "",
        "found": {},
        "redirect_url": "",
    }

    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/125.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        ) as client:
            response = client.get(url)
            result["status"] = response.status_code
            result["redirect_url"] = str(response.url)

            if response.status_code == 200:
                html = response.text
                found = extract_social(html, str(response.url))
                result["found"] = found

    except httpx.TimeoutException:
        result["error"] = "timeout"
    except httpx.ConnectError:
        result["error"] = "connection_error"
    except httpx.HTTPStatusError as e:
        result["error"] = f"http_{e.response.status_code}"
        result["status"] = e.response.status_code
    except Exception as e:
        result["error"] = str(e)[:100]

    return result


def main():
    # Load websites from master
    websites = []
    with open(BASE / "pv_master_unified.csv", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            url = (r.get("website") or "").strip()
            name = (r.get("business_name") or "").strip()
            if url:
                websites.append({"business_name": name, "website": url})

    # Load checkpoint
    done_urls = set()
    results = []
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                done_urls.add(r.get("url", "").strip())
                results.append(r)

    # Filter remaining
    remaining = [w for w in websites if w["website"] not in done_urls]
    print(f"Total websites: {len(websites)}")
    print(f"Already crawled: {len(done_urls)}")
    print(f"Remaining: {len(remaining)}")

    if not remaining:
        print("All done!")
        return

    # Write header if first run
    fieldnames = ["business_name", "url", "status", "error", "redirect_url",
                  "instagram_url", "facebook_url", "whatsapp",
                  "booking_url", "tiktok_url", "youtube_url",
                  "twitter_url", "email"]
    if not RESULTS_FILE.exists():
        with open(RESULTS_FILE, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()

    # Crawl each
    for i, w in enumerate(remaining):
        url = w["website"]
        biz = w["business_name"]
        print(f"[{i+1}/{len(remaining)}] {biz[:40]:40s} {url[:50]}")

        result = crawl_website(url)

        # Build row
        row = {
            "business_name": biz,
            "url": url,
            "status": result["status"],
            "error": result["error"],
            "redirect_url": result["redirect_url"],
            "instagram_url": "",
            "facebook_url": "",
            "whatsapp": "",
            "booking_url": "",
            "tiktok_url": "",
            "youtube_url": "",
            "twitter_url": "",
            "email": "",
        }

        found = result.get("found", {})
        for field in found:
            row[field] = "; ".join(found[field])

        # Append to CSV
        with open(RESULTS_FILE, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writerow(row)

        # Status
        found_count = sum(len(v) for v in found.values())
        if found_count:
            print(f"  -> Found {found_count} links")
        elif result["error"]:
            print(f"  -> Error: {result['error']}")
        else:
            print(f"  -> No social links found (HTTP {result['status']})")

        # Delay between requests (polite)
        if i < len(remaining) - 1:
            delay = random.uniform(1.5, 3.5)
            time.sleep(delay)

    # Summary
    print(f"\nDone. Results in {RESULTS_FILE}")


if __name__ == "__main__":
    main()
