"""
Instagram enrichment via DuckDuckGo search.
Searches for each business without IG using the pattern:
  site:instagram.com "Business Name" Puerto Viejo
"""

import csv
import json
import re
import time
import httpx
import urllib.parse

INPUT_CSV = "pv_within_5km_enriched.csv"
OUTPUT_CSV = "pv_within_5km_enriched2.csv"
LOG_FILE = "ig_enrich_ddg_log.json"


def search_ddg(query: str) -> str | None:
    """Search DuckDuckGo lite and return HTML."""
    client = httpx.Client(
        follow_redirects=True,
        timeout=15.0,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        },
    )
    try:
        resp = client.post(
            "https://lite.duckduckgo.com/lite/",
            data={"q": query},
        )
        if resp.status_code == 200:
            return resp.text
        return None
    except Exception:
        return None
    finally:
        client.close()


def extract_ig_handles(html: str) -> list[str]:
    """Extract Instagram handles from DuckDuckGo search results HTML."""
    handles = set()
    for m in re.finditer(r'instagram\.com/([a-zA-Z0-9_.]+)', html):
        handle = m.group(1).lower()
        # Skip non-business patterns
        if handle in (
            "",
            "p",
            "reel",
            "explore",
            "accounts",
            "oauth",
            "developer",
            "about",
            "download",
            "share",
            "stories",
            "tv",
            "directory",
        ):
            continue
        if len(handle) > 30:
            continue
        handles.add(handle)
    return list(handles)


def main():
    # Load data
    with open(INPUT_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    print(f"Loaded {len(rows)} records", flush=True)

    # Find records without Instagram
    targets = [
        r
        for r in rows
        if not r.get("instagram_handle")
    ]
    print(f"Targets (no IG): {len(targets)}", flush=True)

    # Batch: first, last time, results
    log = []
    now = time.strftime("%Y-%m-%d")
    found_count = 0
    searched_count = 0

    for r in targets:
        name = r.get("business_name", "") or ""
        # Clean up the name (remove " - Playa X, Puerto Viejo, Limon..." suffixes)
        clean_name = re.sub(r"\s*[-–—]\s*(Playa|Puerto|Cahuita|Manzanillo).*$", "", name).strip()
        if not clean_name:
            clean_name = name.split("-")[0].strip()

        # Build search query
        query = f'site:instagram.com "{clean_name}" Puerto Viejo'
        print(f"  Searching: {clean_name[:50]}", flush=True)

        html = search_ddg(query)
        searched_count += 1

        if html:
            handles = extract_ig_handles(html)
            # Filter: prefer handles that are similar to the business name
            best_handle = None
            best_score = 0
            name_lower = clean_name.lower()

            for h in handles:
                # Score: how much of the business name is in the handle
                name_words = set(name_lower.split())
                handle_lower = h.lower()
                overlap = sum(1 for w in name_words if w in handle_lower and len(w) > 2)
                score = overlap / max(len(name_words), 1)
                if score > best_score:
                    best_score = score
                    best_handle = h

            if best_handle:
                r["instagram_handle"] = best_handle
                r["instagram_url"] = f"https://www.instagram.com/{best_handle}/"
                r["instagram_enrich_source"] = "ddg_search"
                r["instagram_enrich_date"] = now
                r["instagram_enrich_confidence"] = "medium" if best_score < 0.5 else "high"
                found_count += 1
                log.append({
                    "business": clean_name,
                    "original": name,
                    "query": query,
                    "found": best_handle,
                    "all_handles": handles,
                    "score": best_score,
                })
                print(f"    FOUND: {best_handle} (score={best_score})", flush=True)

        # Rate limit: be polite to DuckDuckGo
        time.sleep(1.5)

    # Summary
    print(f"\n{'='*50}", flush=True)
    print(f"DUCKDUCKGO IG ENRICHMENT RESULTS", flush=True)
    print(f"{'='*50}", flush=True)
    print(f"  Searched:   {searched_count}", flush=True)
    print(f"  Found new:  {found_count}", flush=True)

    final_with_ig = sum(1 for r in rows if r.get("instagram_handle"))
    print(f"  Final with IG: {final_with_ig} ({final_with_ig/len(rows)*100:.1f}%)", flush=True)
    print(f"  Still without: {len(rows) - final_with_ig}", flush=True)

    # Write enriched CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Written: {OUTPUT_CSV}", flush=True)

    # Write log
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"Log: {LOG_FILE}", flush=True)


if __name__ == "__main__":
    main()
