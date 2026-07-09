"""
Find genuinely new businesses from OSM-only that aren't in the master.
Check by name similarity and flag the real additions.
"""
import csv, re, json
from collections import defaultdict
from pathlib import Path

# Load master
master_names = set()
master_by_slug = {}
with open("pv_master_unified.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        n = row.get("business_name","").strip().lower()
        n = re.sub(r"[^a-z0-9]", "", n)
        master_names.add(n)
        slug = re.sub(r"[^a-z0-9]+", "-", row.get("business_name","").strip().lower())
        master_by_slug[slug] = row

# Load OSM-only
with open("paradisio_app/data/osm_only.csv", encoding="utf-8") as f:
    osm_records = list(csv.DictReader(f))

# Check each OSM name against master
def normalize(n):
    return re.sub(r"[^a-z0-9]", "", n.lower().strip())

def is_in_master(osm_name):
    n = normalize(osm_name)
    if not n or len(n) < 3:
        return True  # skip noise
    # Direct match
    if n in master_names:
        return True
    # Partial match
    for mn in master_names:
        if len(n) > 5 and len(mn) > 5:
            if n in mn or mn in n:
                return True
    return False

new_biz = []
noise = []
for r in osm_records:
    name = r.get("name","").strip()
    if not name or len(name) < 3:
        noise.append(r)
        continue
    # Filter noise: generic names that aren't real businesses
    noise_keywords = ["shopping", "exchange", "policia", "bcr", "banco", "parque", "park", "feria", 
                      "calle", "street", "avenida", "templo", "iglesia", "church", "school",
                      "escuela", "colegio", "plaza", "rotonda", "terminal", "parada", "bus stop"]
    if normalize(name) in [normalize(k) for k in noise_keywords]:
        noise.append(r)
        continue
    
    if not is_in_master(name):
        # Check if this looks like a commercial establishment (has valid tags)
        tags_str = r.get("tags","")
        commercial_tags = ["shop", "tourism", "amenity", "craft", "office", "leisure"]
        try:
            tags = json.loads(tags_str) if tags_str else {}
        except:
            tags = {}
        is_commercial = any(t in tags for t in commercial_tags) or r.get("category","") != "unknown"
        
        new_biz.append({
            "name": name,
            "category": r.get("category",""),
            "lat": r.get("lat",""),
            "lon": r.get("lon",""),
            "phone": r.get("phone",""),
            "website": r.get("website",""),
            "email": r.get("email",""),
            "hours": r.get("opening_hours",""),
            "distance_km": r.get("distance_km",""),
            "is_commercial": is_commercial,
            "tags": tags_str[:200],
        })

print(f"Total OSM-only: {len(osm_records)}")
print(f"Noise (generic/non-commercial): {len(noise)}")
print(f"Already in master: {len(osm_records) - len(new_biz) - len(noise)}")
print(f"Genuinely new candidates: {len(new_biz)}")

commercial = [b for b in new_biz if b["is_commercial"]]
print(f"  Commercial: {len(commercial)}")
non_commercial = [b for b in new_biz if not b["is_commercial"]]
print(f"  Non-commercial: {len(non_commercial)}")

print(f"\nNew commercial candidates by category:")
cats = defaultdict(int)
for b in commercial:
    cats[b["category"]] += 1
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {c:20s}: {n}")

print(f"\nSample new commercial businesses:")
for b in commercial[:20]:
    contact = b.get("phone","") or b.get("website","") or b.get("email","") or ""
    print(f"  {b['name'][:45]:45s} | {b['category']:15s} | {b['distance_km']} km | {contact[:25]}")

# Save new commercial candidates
with open("paradisio_app/data/osm_new_candidates.csv", "w", newline="", encoding="utf-8") as f:
    fields = ["name", "category", "lat", "lon", "phone", "website", "email", "hours", "distance_km"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for b in sorted(commercial, key=lambda x: x["category"]):
        w.writerow({k: b.get(k,"") for k in fields})
print(f"\nSaved {len(commercial)} candidates to paradisio_app/data/osm_new_candidates.csv")
