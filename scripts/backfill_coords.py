"""
Backfill missing lat/lng in pv_master_unified.csv using area-based approximation.

For each area, calculates the mean center from existing businesses that have
coordinates, then applies that center to any business in the same area that
is missing lat/lng. For areas with zero existing coordinates (Bribri, Gandoca),
uses known town-center coordinates.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "pv_master_unified.csv"

# Known town centers for areas with zero coordinate coverage
KNOWN_CENTERS = {
    "Bribri":     (9.6250, -82.8750),
    "Gandoca":    (9.5900, -82.6400),
    "Hone Creek": (9.6550, -82.8000),
    "Manzanillo": (9.6300, -82.6600),
    "Cahuita":    (9.7400, -82.8500),
    "Sixaola":    (9.5000, -82.6200),
    "Playa Negra":   (9.6550, -82.7700),
    "Playa Cocles":  (9.6450, -82.7200),
    "Playa Chiquita": (9.6400, -82.6800),
    "Punta Uva":     (9.6400, -82.6700),
    "Puerto Viejo":  (9.6550, -82.7500),
    "Cocles":        (9.6250, -82.7100),
}

# Step 1: read CSV, compute area centers from existing coords
area_data = defaultdict(lambda: {"lats": [], "lngs": [], "count": 0, "missing": []})

rows = []
with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        rows.append(row)
        area = (row.get("area") or "").strip()
        lat = (row.get("latitude") or "").strip()
        lng = (row.get("longitude") or "").strip()

        if lat and lng:
            area_data[area]["lats"].append(float(lat))
            area_data[area]["lngs"].append(float(lng))
            area_data[area]["count"] += 1
        else:
            area_data[area]["missing"].append(row)

# Step 2: compute centers
area_centers = {}
for area, d in area_data.items():
    if d["count"] > 0:
        area_centers[area] = (
            sum(d["lats"]) / d["count"],
            sum(d["lngs"]) / d["count"],
        )
    elif area in KNOWN_CENTERS:
        area_centers[area] = KNOWN_CENTERS[area]
    else:
        area_centers[area] = KNOWN_CENTERS.get(area, (9.65, -82.75))

# Step 3: backfill
backfilled = 0
for area, d in area_data.items():
    center = area_centers.get(area)
    if not center:
        continue
    for row in d["missing"]:
        row["latitude"] = f"{center[0]:.7f}"
        row["longitude"] = f"{center[1]:.7f}"
        backfilled += 1

# Step 4: write
with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Backfilled {backfilled} records with area-approximate coordinates")
for area, center in sorted(area_centers.items()):
    d = area_data[area]
    if d["missing"]:
        print(f"  {area:20s} -> {center[0]:.5f}, {center[1]:.5f}  ({len(d['missing'])} records)")
print(f"\nDone. {sum(len(d['missing']) for d in area_data.values()) - backfilled} still empty (should be 0)")
