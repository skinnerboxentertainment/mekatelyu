"""
Cross-reference PVS businesses with OpenStreetMap data.
Produces: both, OSM only, PVS only, with confidence scores.
"""

import csv
import json
import re
import math
from collections import defaultdict

PVS_CSV = "pv_within_5km.csv"
OSM_FILE = "osm_data.json"
OUTPUT_BOTH = "pv_osm_both.csv"
OUTPUT_OSM_ONLY = "pv_osm_osmonly.csv"
OUTPUT_PVS_ONLY = "pv_osm_pvsonly.csv"


def normalize_name(name: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def token_similarity(a: str, b: str) -> float:
    """Jaccard similarity on word tokens."""
    a_tokens = set(normalize_name(a).split())
    b_tokens = set(normalize_name(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(intersection) / len(union)


def name_contains(a: str, b: str) -> bool:
    """Check if normalized names largely overlap."""
    na = normalize_name(a)
    nb = normalize_name(b)
    # One is a substring of the other
    if na in nb or nb in na:
        return True
    # Shared initial word match (e.g., "Hotel Banana Azul" == "Banana Azul Hotel")
    a_words = na.split()
    b_words = nb.split()
    shared = set(a_words) & set(b_words)
    smaller = min(len(a_words), len(b_words))
    if smaller <= 2:
        return len(shared) >= smaller
    return len(shared) >= smaller - 1


def osm_category(tags: dict) -> str:
    """Determine PVS-like category from OSM tags."""
    if "shop" in tags:
        return "shopping"
    if "tourism" in tags:
        t = tags["tourism"]
        if t in ("hotel", "guest_house", "motel", "chalet", "apartment"):
            return "hotel"
        if t == "hostel":
            return "hostel"
        if t in ("camp_site", "caravan_site"):
            return "vacation_rental"
        if t in ("attraction", "viewpoint", "information", "museum", "zoo"):
            return "tour_company"
    if "amenity" in tags:
        a = tags["amenity"]
        if a in ("restaurant", "fast_food", "cafe", "bar", "pub", "ice_cream"):
            return "restaurant"
        if a in ("bank", "atm", "pharmacy", "clinic", "hospital", "dentist",
                 "veterinary", "school", "police", "post_office", "car_rental",
                 "car_wash", "fuel", "bicycle_rental", "laundry"):
            return "services"
        if a in ("marketplace", "shopping_centre"):
            return "shopping"
    return "unknown"


def main():
    # Load PVS data
    pvs_records = []
    with open(PVS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("business_name") or "").strip()
            if name:
                pvs_records.append(row)
    print(f"PVS records: {len(pvs_records)}", flush=True)

    # Load OSM data
    with open(OSM_FILE, encoding="utf-8") as f:
        osm_raw = json.load(f)
    osm_records = []
    for e in osm_raw.get("elements", []):
        tags = e.get("tags", {})
        name = (tags.get("name") or "").strip()
        if not name:
            continue
        lat = e.get("lat")
        lon = e.get("lon")
        if lat is None or lon is None:
            continue
        osm_records.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "tags": tags,
            "osm_type": e["type"],
            "osm_id": e["id"],
            "category": osm_category(tags),
        })
    print(f"OSM records: {len(osm_records)}", flush=True)

    # ---- Step 1: Match PVS -> OSM ----
    matched_pvs = set()
    matched_osm = set()
    matches = []

    # Index OSM by normalized name prefix
    osm_by_prefix = defaultdict(list)
    for o in osm_records:
        norm = normalize_name(o["name"])
        # Index by first word of normalized name
        words = norm.split()
        for w in words[:2]:
            if len(w) > 2:
                osm_by_prefix[w].append(o)

    for pvs in pvs_records:
        pvs_name = pvs["business_name"]
        pvs_norm = normalize_name(pvs_name)
        best_match = None
        best_score = 0.0

        # Collect candidates by prefix match
        candidates = set()
        words = pvs_norm.split()
        for w in words:
            for o in osm_by_prefix.get(w, []):
                candidates.add(o["osm_id"])

        for oid in candidates:
            o = next(o for o in osm_records if o["osm_id"] == oid)
            oname = o["name"]
            score = token_similarity(pvs_name, oname)
            # Boost if names contain each other
            if name_contains(pvs_name, oname):
                score = max(score, 0.7)
            if score > best_score:
                best_score = score
                best_match = o

        if best_match and best_score >= 0.5:
            matched_pvs.add(id(pvs))
            matched_osm.add(best_match["osm_id"])
            matches.append({
                "pvs_name": pvs_name,
                "osm_name": best_match["name"],
                "osm_category": best_match["category"],
                "osm_lat": best_match["lat"],
                "osm_lon": best_match["lon"],
                "match_score": round(best_score, 3),
                "pvs_category": pvs["category"],
                "pvs_area": pvs["area"],
                "pvs_instagram": pvs.get("instagram_handle", ""),
                "pvs_phone": pvs.get("phone", ""),
                "pvs_verified": pvs.get("verified_date", ""),
                "pvs_url": pvs["url"],
            })

    print(f"Matched (both): {len(matches)}", flush=True)

    # ---- Step 2: PVS only ----
    pvs_only = [r for r in pvs_records if id(r) not in matched_pvs]
    print(f"PVS only: {len(pvs_only)}", flush=True)

    # ---- Step 3: OSM only ----
    osm_only = [r for r in osm_records if r["osm_id"] not in matched_osm]
    print(f"OSM only: {len(osm_only)}", flush=True)

    # ---- Step 4: Write outputs ----

    # Both
    fields_both = [
        "pvs_name", "osm_name", "match_score", "pvs_category", "osm_category",
        "pvs_area", "osm_lat", "osm_lon", "pvs_instagram",
        "pvs_phone", "pvs_verified", "pvs_url",
    ]
    with open(OUTPUT_BOTH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields_both)
        w.writeheader()
        for m in sorted(matches, key=lambda x: x["pvs_category"]):
            w.writerow(m)
    print(f"Written: {OUTPUT_BOTH} ({len(matches)} records)", flush=True)

    # OSM only
    fields_osm = ["name", "category", "lat", "lon", "tags"]
    with open(OUTPUT_OSM_ONLY, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields_osm)
        w.writeheader()
        for o in sorted(osm_only, key=lambda x: x["category"]):
            w.writerow({
                "name": o["name"],
                "category": o["category"],
                "lat": o["lat"],
                "lon": o["lon"],
                "tags": json.dumps(o["tags"], ensure_ascii=False),
            })
    print(f"Written: {OUTPUT_OSM_ONLY} ({len(osm_only)} records)", flush=True)

    # PVS only
    fields_pvs = [
        "business_name", "category", "area", "latitude", "longitude",
        "instagram_handle", "instagram_url", "phone", "normalized_phone",
        "website", "facebook_url", "google_maps_cid", "verified_date",
        "url",
    ]
    with open(OUTPUT_PVS_ONLY, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields_pvs)
        w.writeheader()
        for r in sorted(pvs_only, key=lambda x: x["category"]):
            w.writerow({k: r.get(k, "") for k in fields_pvs})
    print(f"Written: {OUTPUT_PVS_ONLY} ({len(pvs_only)} records)", flush=True)

    # ---- Summary ----
    print("\n" + "=" * 50)
    print("CROSS-REFERENCE SUMMARY")
    print("=" * 50)
    print(f"  PVS within 5 km:    {len(pvs_records)}")
    print(f"  OSM within 5 km:    {len(osm_records)}")
    print(f"  In both:            {len(matches)} ({len(matches)/len(pvs_records)*100:.1f}% of PVS)")
    print(f"  PVS only:           {len(pvs_only)} ({len(pvs_only)/len(pvs_records)*100:.1f}%)")
    print(f"  OSM only:           {len(osm_only)} ({len(osm_only)/len(osm_records)*100:.1f}% of OSM)")

    # By category
    print("\nBy category (matched):")
    cat_counts = defaultdict(int)
    for m in matches:
        cat_counts[m["pvs_category"]] += 1
    for c in sorted(cat_counts.keys()):
        pvs_cat_total = sum(1 for r in pvs_records if r["category"] == c)
        print(f"  {c:20s}: {cat_counts[c]:3d} matched / {pvs_cat_total:3d} total ({cat_counts[c]/pvs_cat_total*100:.0f}%)")

    print("\nOSM-only (potential additions):")
    osm_cat_counts = defaultdict(int)
    for o in osm_only:
        osm_cat_counts[o["category"]] += 1
    for c in sorted(osm_cat_counts.keys()):
        print(f"  {c:20s}: {osm_cat_counts[c]}")

    # Sample OSM-only names
    print("\nSample OSM-only names:")
    for o in osm_only[:15]:
        tags_str = "; ".join(f"{k}={v}" for k, v in o["tags"].items()
                            if k in ("shop", "tourism", "amenity", "name"))
        print(f"  {o['name'][:50]:50s} | {o['category']:15s} | {tags_str[:60]}")


if __name__ == "__main__":
    main()
