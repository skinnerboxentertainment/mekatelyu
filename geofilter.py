"""
Geofilter: add coordinates to listings from cached category page arrays,
then filter to 5 km radius of Puerto Viejo center.
"""

import csv
import math
import re
import sqlite3
from collections import defaultdict
from urllib.parse import urlparse

DB_PATH = "pvscraper_full.db"
OUTPUT_FILTERED = "pv_within_5km.csv"
OUTPUT_FULL = "pv_with_coordinates.csv"

ORIGIN_LAT = 9.6554
ORIGIN_LON = -82.7533

# Area centers for listings without coordinates
AREA_CENTERS = {
    "Puerto Viejo": (9.6554, -82.7533),
    "Playa Negra": (9.660, -82.765),
    "Cocles": (9.642, -82.748),
    "Playa Chiquita": (9.632, -82.745),
    "Punta Uva": (9.622, -82.737),
    "Manzanillo": (9.630, -82.660),
    "Cahuita": (9.735, -82.845),
    "Hone Creek": (9.675, -82.820),
    "Bribri": (9.628, -82.860),
    "Gandoca": (9.578, -82.608),
    "Sixaola": (9.530, -82.630),
}

# Areas that must always be included regardless of computed distance
INCLUDED_AREAS = {"Puerto Viejo", "Playa Negra", "Cocles", "Playa Chiquita", "Punta Uva", "Hone Creek"}

# Areas that must always be excluded regardless of computed distance
EXCLUDED_AREAS = {"Sixaola", "Gandoca", "Bribri", "Manzanillo", "Cahuita"}


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def parse_coordinate_arrays(html: str) -> tuple[list[float], list[float]]:
    """Parse aLats and aLngs/aLongs JavaScript arrays from category page HTML."""
    lats = []
    lngs = []
    lat_match = re.search(r"var aLats\s*=\s*\[([^\]]+)\]", html)
    lng_match = re.search(r"var a(?:Lngs|Longs)\s*=\s*\[([^\]]+)\]", html)
    if lat_match:
        lats = [float(x.strip()) for x in lat_match.group(1).split(",") if x.strip()]
    if lng_match:
        lngs = [float(x.strip()) for x in lng_match.group(1).split(",") if x.strip()]
    return lats, lngs


def listing_order_from_html(html: str) -> list[str]:
    """Extract listing URLs from a category page in DOM order."""
    urls = []
    for m in re.finditer(r'puertoviejosatellite\.com(/en/[a-z0-9-]+/[a-z0-9-]+/)', html):
        url = f"https://www.puertoviejosatellite.com{m.group(1)}"
        if url not in urls:
            urls.append(url)
    return urls


def scrape_coords_from_maps_url(cid: str) -> tuple[float, float] | None:
    """Fetch a Google Maps URL and scrape OG meta tags for coordinates."""
    import httpx
    try:
        resp = httpx.get(
            f"https://maps.google.com/?cid={cid}",
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
        if resp.status_code == 200:
            html = resp.text
            lat_m = re.search(r'<meta\s+property="og:latitude"\s+content="([^"]+)"', html, re.I)
            lng_m = re.search(r'<meta\s+property="og:longitude"\s+content="([^"]+)"', html, re.I)
            if lat_m and lng_m:
                return float(lat_m.group(1)), float(lng_m.group(1))
            # Try JSON-LD
            jd = re.search(
                r'<script type="application/ld\+json">([^<]+)</script>', html, re.DOTALL
            )
            if jd:
                import json
                try:
                    data = json.loads(jd.group(1))
                    if isinstance(data, dict):
                        geo = data.get("geo", {})
                        if geo.get("latitude") and geo.get("longitude"):
                            return float(geo["latitude"]), float(geo["longitude"])
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ---- Step 1: Collect all listings ----
    listings = conn.execute("SELECT * FROM listings").fetchall()
    total = len(listings)
    print(f"Total listings in DB: {total}")

    # ---- Step 2: Parse coordinate arrays from cached category pages ----
    category_pages = {
        "hotel": "/en/hotels/",
        "hostel": "/en/hostels/",
        "vacation_rental": "/en/vacation-rentals/",
        "restaurant": "/en/restaurants/",
        "shopping": "/en/shopping/",
        "services": "/en/services/",
        "tour_company": "/en/tour-companies/",
        "real_estate": "/en/real-estate/",
    }

    # Map listing URL -> (lat, lon, source)
    coords: dict[str, tuple[float, float, str]] = {}

    for cat_name, path in category_pages.items():
        row = conn.execute(
            "SELECT html FROM raw_html_cache WHERE url LIKE ?", (f"%{path}%",)
        ).fetchone()
        if not row:
            print(f"  WARNING: No cached page for {cat_name}")
            continue
        html = row["html"]
        lats, lngs = parse_coordinate_arrays(html)
        urls = listing_order_from_html(html)
        # The arrays should match listing order in the page
        # But we need to match by position. The URLs we extract from the page
        # should be in the same order as lats/lngs arrays.
        if lats and len(lats) == len(lngs):
            # Use category + (positional match) to pair coords with listings
            # We stored the enumeration order in the enumerator (category page order).
            # The arrays match the order listings appear on the page.
            cat_listings = [l for l in listings if l["category"] == cat_name]
            # We need to match by POSITION within the category
            max_pairs = min(len(lats), len(cat_listings))
            for i in range(max_pairs):
                url = cat_listings[i]["url"]
                coords[url] = (lats[i], lngs[i], "array")
            print(f"  {cat_name}: {len(lats)} lats, matched to {max_pairs} listings")

    # ---- Step 3: Maps URL fallback for unmatched CIDs ----
    unmatched = [l for l in listings if l["url"] not in coords and l["google_maps_cid"]]
    print(f"\nUnmatched listings with CID: {len(unmatched)}")
    for i, listing in enumerate(unmatched):
        cid = listing["google_maps_cid"]
        result = scrape_coords_from_maps_url(cid)
        if result:
            coords[listing["url"]] = (result[0], result[1], "maps_url")
        if (i + 1) % 20 == 0:
            print(f"  ... {i+1}/{len(unmatched)} Maps URL lookups done")
        import time
        time.sleep(1.0)

    # ---- Step 4: Area center fallback for remaining ----
    no_coord = [l for l in listings if l["url"] not in coords]
    print(f"\nRemaining without coordinates: {len(no_coord)}")
    for listing in no_coord:
        area = listing["area"] or "unknown"
        if area in AREA_CENTERS:
            lat, lon = AREA_CENTERS[area]
            coords[listing["url"]] = (lat, lon, "area_label")
        else:
            coords[listing["url"]] = (9.6554, -82.7533, "default")

    # ---- Step 5: Apply geofilter ----
    filtered = []
    excluded = []
    for l in listings:
        url = l["url"]
        lat, lon, source = coords.get(url, (9.6554, -82.7533, "unknown"))
        distance = haversine_km(lat, lon, ORIGIN_LAT, ORIGIN_LON)
        area = l["area"] or "unknown"

        if area in EXCLUDED_AREAS:
            geofilter = "fail"
            reason = f"area_excluded:{area}"
        elif area in INCLUDED_AREAS:
            geofilter = "pass"
            reason = f"area_included:{area}"
        elif distance <= 5.0:
            geofilter = "pass"
            reason = f"within_5km:{distance:.2f}km"
        else:
            geofilter = "fail"
            reason = f"beyond_5km:{distance:.2f}km"

        record = {
            "business_name": l["business_name"],
            "category": l["category"],
            "area": l["area"],
            "latitude": lat,
            "longitude": lon,
            "distance_km": round(distance, 3),
            "geofilter": geofilter,
            "geofilter_reason": reason,
            "coordinate_source": source,
            "phone": l["phone"],
            "normalized_phone": l["normalized_phone"],
            "website": l["website"],
            "instagram_handle": l["instagram_handle"],
            "instagram_url": l["instagram_url"],
            "facebook_url": l["facebook_url"],
            "google_maps_cid": l["google_maps_cid"],
            "verified_date": l["verified_date"],
            "operating_status": l["operating_status"],
            "url": l["url"],
        }
        if geofilter == "pass":
            filtered.append(record)
        else:
            excluded.append(record)

    print(f"\n{'='*50}")
    print(f"Geofilter Results")
    print(f"{'='*50}")
    print(f"  Within 5 km:  {len(filtered)}")
    print(f"  Excluded:     {len(excluded)}")
    print(f"  Total:        {total}")

    # Summary by area
    print(f"\nBy area:")
    area_counts = defaultdict(lambda: {"pass": 0, "fail": 0, "total": 0})
    for r in filtered:
        area_counts[r["area"]]["pass"] += 1
        area_counts[r["area"]]["total"] += 1
    for r in excluded:
        area_counts[r["area"]]["fail"] += 1
        area_counts[r["area"]]["total"] += 1
    for area in sorted(area_counts.keys()):
        c = area_counts[area]
        print(f"  {area:20s}: {c['pass']:3d} in / {c['fail']:3d} out (of {c['total']})")

    # Summary by category
    print(f"\nBy category (within 5 km):")
    cat_counts = defaultdict(int)
    for r in filtered:
        cat_counts[r["category"]] += 1
    for cat in sorted(cat_counts.keys()):
        print(f"  {cat:20s}: {cat_counts[cat]}")

    # ---- Step 6: Write results to CSV ----
    fields = [
        "business_name", "category", "area", "latitude", "longitude",
        "distance_km", "geofilter", "geofilter_reason", "coordinate_source",
        "phone", "normalized_phone", "website", "instagram_handle",
        "instagram_url", "facebook_url", "google_maps_cid",
        "verified_date", "operating_status", "url",
    ]

    # Full CSV with coordinates + geofilter
    with open(OUTPUT_FULL, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in filtered:
            w.writerow(r)
        for r in excluded:
            w.writerow(r)
    print(f"\nFull output: {OUTPUT_FULL} ({len(filtered) + len(excluded)} records)")

    # Filtered CSV (within 5 km only)
    with open(OUTPUT_FILTERED, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in filtered:
            w.writerow(r)
    print(f"Filtered output: {OUTPUT_FILTERED} ({len(filtered)} records)")

    conn.close()


if __name__ == "__main__":
    main()
