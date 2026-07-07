"""Build the stealth search target CSV — 134 grid names first, then 31 OSM, then 100 PVS."""
import csv, re

GRID_CSV = "grid_discoveries_ig_enriched.csv"
OSM_CSV = "pv_within_5km_verified_additions_enriched.csv"
PVS_CSV = "pv_within_5km_enriched_b.csv"
OUTPUT = "stealth_targets.csv"

def load_names(path, key="business_name"):
    results = []
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                name = (r.get(key) or "").strip()
                if not name:
                    continue
                lat = (r.get("latitude") or "").strip()
                lon = (r.get("longitude") or "").strip()
                cid = (r.get("google_maps_cid") or "").strip()
                results.append({
                    "business_name": name,
                    "source": path,
                    "latitude": lat,
                    "longitude": lon,
                    "existing_cid": cid,
                })
    except:
        pass
    return results

# Grid names — no coords, no CIDs (priority 1)
grid = load_names(GRID_CSV)
grid_no_coords = [r for r in grid if not (r["latitude"] and r["longitude"])]
# Also include grid names that have coords but no CID
grid_no_cid = [r for r in grid if r["latitude"] and r["longitude"] and not r["existing_cid"]]
print(f"Grid names (no coords): {len(grid_no_coords)}")
print(f"Grid names (no CID):   {len(grid_no_cid)}")

# OSM additions — have coords but no CIDs (priority 2)
osm = load_names(OSM_CSV)
osm_no_cid = [r for r in osm if not r["existing_cid"]]
print(f"OSM no CID:            {len(osm_no_cid)}")

# PVS master — have coords but no CIDs (priority 3)
pvs = load_names(PVS_CSV)
pvs_no_cid = [r for r in pvs if not r["existing_cid"]]
print(f"PVS no CID:            {len(pvs_no_cid)}")

# Build prioritized list
targets = []
targets.extend(grid_no_coords)
targets.extend(grid_no_cid)
targets.extend(osm_no_cid)
targets.extend(pvs_no_cid)

print(f"\nTotal targets: {len(targets)}")

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["business_name", "source", "latitude", "longitude", "existing_cid"])
    w.writeheader()
    for t in targets:
        w.writerow(t)
print(f"Written: {OUTPUT}")
