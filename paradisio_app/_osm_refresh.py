"""
Refresh OSM data and cross-reference against the 750-record master dataset.
Targets the 131 uncategorized records specifically for enrichment.
"""
import csv, json, math, re, sys
from collections import defaultdict
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

PV_CENTER = (9.655, -82.753)
RADIUS_KM = 5.5  # slightly larger than master to catch edge candidates

OVERPAY_URL = "https://overpass-api.de/api/interpreter"
OSM_OUTPUT = Path("paradisio_app/data/osm_raw.json")

MASTER_CSV = Path("pv_master_unified.csv")
BOTH_OUTPUT = Path("paradisio_app/data/osm_both.csv")
OSM_ONLY_OUTPUT = Path("paradisio_app/data/osm_only.csv")
MASTER_ONLY_OUTPUT = Path("paradisio_app/data/osm_master_only.csv")


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def fetch_osm():
    """Query Overpass API for businesses within the radius."""
    lat, lon = PV_CENTER
    query = f"""
    [out:json][timeout:180];
    (
      node["name"](around:{RADIUS_KM*1000},{lat},{lon});
      way["name"](around:{RADIUS_KM*1000},{lat},{lon});
      relation["name"](around:{RADIUS_KM*1000},{lat},{lon});
    );
    out center tags;
    """
    print("Fetching OSM data from Overpass API...")
    headers = {"User-Agent": "Paradisio/1.0 (business directory; +https://github.com/skinnerboxentertainment/mekatelyu)", "Accept": "application/json"}
    resp = httpx.get(OVERPAY_URL, params={"data": query}, headers=headers, timeout=180)
    print(f"Status: {resp.status_code}, Size: {len(resp.text)} bytes")
    data = resp.json()
    with open(OSM_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {OSM_OUTPUT}")
    return data


def normalize_name(name):
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def name_similarity(a, b):
    na = normalize_name(a)
    nb = normalize_name(b)
    if na in nb or nb in na:
        return True
    a_words = set(na.split())
    b_words = set(nb.split())
    shared = a_words & b_words
    smaller = min(len(a_words), len(b_words))
    if smaller <= 2:
        return len(shared) >= smaller
    return len(shared) >= smaller - 1


def osm_category(tags):
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
                 "car_wash", "fuel", "bicycle_rental", "laundry", "parking"):
            return "services"
        if a in ("marketplace", "shopping_centre"):
            return "shopping"
    return "unknown"


def main():
    # Step 1: Fetch or load OSM data
    osm_data = fetch_osm()
    
    # Step 2: Parse OSM records
    osm_records = []
    for e in osm_data.get("elements", []):
        tags = e.get("tags", {})
        name = (tags.get("name") or "").strip()
        if not name:
            continue
        lat = e.get("lat") or (e.get("center") or {}).get("lat")
        lon = e.get("lon") or (e.get("center") or {}).get("lon")
        if lat is None or lon is None:
            continue
        dist = haversine(PV_CENTER[0], PV_CENTER[1], lat, lon)
        if dist > RADIUS_KM:
            continue
        osm_records.append({
            "name": name,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "tags": tags,
            "category": osm_category(tags),
            "distance_km": round(dist, 3),
            "phone": tags.get("phone", ""),
            "website": tags.get("website", ""),
            "email": tags.get("email", ""),
            "opening_hours": tags.get("opening_hours", ""),
            "osm_type": e["type"],
            "osm_id": e["id"],
        })
    
    print(f"\nOSM records within {RADIUS_KM} km: {len(osm_records)}")
    
    # Step 3: Load master dataset (750 records)
    master = []
    with open(MASTER_CSV, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = (row.get("business_name") or "").strip()
            if name:
                master.append(row)
    print(f"Master records: {len(master)}")
    
    # Step 4: Match master to OSM
    matched_master = set()
    matched_osm = set()
    matches = []
    
    # Index OSM by prefix for faster lookup
    osm_by_prefix = defaultdict(list)
    for o in osm_records:
        norm = normalize_name(o["name"])
        for w in norm.split()[:2]:
            if len(w) > 2:
                osm_by_prefix[w].append(o)
    
    for m in master:
        mname = m["business_name"]
        mnorm = normalize_name(mname)
        candidates = set()
        for w in mnorm.split():
            for o in osm_by_prefix.get(w, []):
                candidates.add(o["osm_id"])
        
        best = None
        for oid in candidates:
            o = next(o for o in osm_records if o["osm_id"] == oid)
            if name_similarity(mname, o["name"]):
                best = o
                break
        
        if best:
            matched_master.add(id(m))
            matched_osm.add(best["osm_id"])
            matches.append({
                "master_name": mname,
                "master_category": m.get("category", ""),
                "master_area": m.get("area", ""),
                "osm_name": best["name"],
                "osm_category": best["category"],
                "osm_lat": best["lat"],
                "osm_lon": best["lon"],
                "osm_phone": best["phone"],
                "osm_website": best["website"],
                "osm_email": best["email"],
                "osm_hours": best["opening_hours"],
            })
    
    print(f"Matched (both): {len(matches)}")
    
    # Step 5: Master-only (not found in OSM)
    master_only = [r for r in master if id(r) not in matched_master]
    print(f"Master only: {len(master_only)}")
    
    # Step 6: OSM-only (not in master)
    osm_only = [r for r in osm_records if r["osm_id"] not in matched_osm]
    print(f"OSM only: {len(osm_only)}")
    
    # Step 7: Write outputs
    both_fields = ["master_name", "master_category", "master_area", "osm_name", "osm_category", "osm_lat", "osm_lon", "osm_phone", "osm_website", "osm_email", "osm_hours"]
    with open(BOTH_OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=both_fields)
        w.writeheader()
        for m in sorted(matches, key=lambda x: x["master_name"]):
            w.writerow(m)
    print(f"Written: {BOTH_OUTPUT} ({len(matches)} records)")
    
    osm_fields = ["name", "category", "lat", "lon", "phone", "website", "email", "opening_hours", "distance_km", "tags"]
    with open(OSM_ONLY_OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=osm_fields)
        w.writeheader()
        for o in sorted(osm_only, key=lambda x: x["category"]):
            w.writerow({k: o.get(k, "") for k in osm_fields})
    print(f"Written: {OSM_ONLY_OUTPUT} ({len(osm_only)} records)")
    
    master_fields = ["business_name", "category", "area", "latitude", "longitude", "phone", "normalized_phone", "instagram_handle", "facebook_url", "website", "google_maps_cid"]
    with open(MASTER_ONLY_OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=master_fields)
        w.writeheader()
        for r in sorted(master_only, key=lambda x: x.get("category","")):
            w.writerow({k: r.get(k, "") for k in master_fields})
    print(f"Written: {MASTER_ONLY_OUTPUT} ({len(master_only)} records)")
    
    # Summary
    print(f"\n{'='*50}")
    print("OSM CROSS-REFERENCE SUMMARY")
    print(f"{'='*50}")
    print(f"  Master dataset:     {len(master)}")
    print(f"  OSM within radius:  {len(osm_records)}")
    print(f"  In both:            {len(matches)}")
    print(f"  Master only:        {len(master_only)}")
    print(f"  OSM only:           {len(osm_only)}")
    
    # Check uncategorized master records
    uncat = [r for r in master_only if not r.get("category","").strip()]
    if uncat:
        print(f"\n  Uncategorized in master-only: {len(uncat)}")
        for r in uncat[:10]:
            print(f"    {r.get('business_name','')[:60]}")
    
    # OSM-only categories
    print("\nOSM-only by category:")
    cat_counts = defaultdict(int)
    for o in osm_only:
        cat_counts[o["category"]] += 1
    for c in sorted(cat_counts.keys()):
        print(f"  {c:20s}: {cat_counts[c]}")
    
    print("\nSample OSM-only names:")
    for o in osm_only[:20]:
        tags_str = "; ".join(f"{k}={v}" for k, v in o["tags"].items() if k in ("shop","tourism","amenity","name"))
        print(f"  {o['name'][:50]:50s} | {o['category']:15s} | {o['distance_km']} km")


if __name__ == "__main__":
    main()
