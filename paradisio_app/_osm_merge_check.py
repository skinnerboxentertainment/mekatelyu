"""
Check OSM new candidates against existing businesses.json and maps_enrich.json
to find true new businesses vs. name-mismatch duplicates.
Uses proximity matching (within 30m) and name similarity.
"""
import csv, json, re, math
from collections import defaultdict
from pathlib import Path

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def normalize(n):
    return re.sub(r"[^a-z0-9]", "", n.lower().strip())

# Load existing businesses
with open("docs/paradisio_app/data/businesses.json", encoding="utf-8") as f:
    existing = json.load(f)
print(f"Existing businesses: {len(existing)}")

# Load OSM candidates
with open("paradisio_app/data/osm_new_candidates.csv", encoding="utf-8") as f:
    candidates = list(csv.DictReader(f))
print(f"OSM candidates: {len(candidates)}")

# Proximity match
true_new = []
matched_existing = []
for c in candidates:
    clat = c.get("lat","").strip()
    clon = c.get("lon","").strip()
    if not clat or not clon:
        true_new.append(c)
        continue
    clat, clon = float(clat), float(clon)
    cnorm = normalize(c["name"])
    
    found_match = False
    for e in existing:
        elat = e.get("lat","")
        elon = e.get("lng","")
        if elat and elon:
            dist = haversine(clat, clon, float(elat), float(elon))
            if dist < 30:  # within 30 meters
                ename = normalize(e.get("name",""))
                # Check name similarity
                if cnorm in ename or ename in cnorm or len(set(cnorm.split()) & set(ename.split())) > 1:
                    matched_existing.append({"osm": c, "existing": e, "distance": round(dist, 1)})
                    found_match = True
                    break
    
    if not found_match:
        true_new.append(c)

true_new_sorted = sorted(true_new, key=lambda x: x.get("category",""))

print(f"\nMatched to existing (proximity + name): {len(matched_existing)}")
print(f"Truly new candidates: {len(true_new)}")
print(f"\nTruly new by category:")
cats = defaultdict(int)
for c in true_new:
    cats[c.get("category","")] += 1
for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {cat:20s}: {n}")

print(f"\nSample truly new:")
for c in true_new[:20]:
    contact = c.get("phone","") or c.get("website","") or ""
    print(f"  {c['name'][:45]:45s} | {c['category']:15s} | {c.get('distance_km','')} km | {contact[:30]}")

# Save truly new candidates
with open("paradisio_app/data/osm_truly_new.csv", "w", newline="", encoding="utf-8") as f:
    fields = ["name", "category", "lat", "lon", "phone", "website", "email", "hours", "distance_km"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for c in true_new_sorted:
        w.writerow({k: c.get(k,"") for k in fields})
print(f"\nSaved {len(true_new)} truly new candidates to paradisio_app/data/osm_truly_new.csv")
