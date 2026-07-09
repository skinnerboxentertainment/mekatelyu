"""
Analyze the 418 OSM-only records: what categories, contact data, coordinates quality.
"""
import csv, json
from collections import defaultdict
from pathlib import Path

with open("paradisio_app/data/osm_only.csv", encoding="utf-8") as f:
    records = list(csv.DictReader(f))

print(f"Total OSM-only records: {len(records)}\n")

# Category breakdown
cats = defaultdict(int)
for r in records:
    cats[r.get("category","unknown")] += 1
print("By category:")
for c, n in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"  {c:20s}: {n}")

# Contact data availability
has_phone = sum(1 for r in records if r.get("phone","").strip())
has_website = sum(1 for r in records if r.get("website","").strip())
has_email = sum(1 for r in records if r.get("email","").strip())
has_coords = sum(1 for r in records if r.get("lat","").strip() and r.get("lon","").strip())
has_hours = sum(1 for r in records if r.get("opening_hours","").strip())

print(f"\nContact data:")
print(f"  Has phone:      {has_phone}")
print(f"  Has website:    {has_website}")
print(f"  Has email:      {has_email}")
print(f"  Has coordinates:{has_coords}")
print(f"  Has hours:      {has_hours}")

# Distance distribution
dists = [float(r.get("distance_km", 99)) for r in records if r.get("distance_km","").strip()]
if dists:
    print(f"\nDistance from PV center:")
    print(f"  Min: {min(dists):.2f} km, Max: {max(dists):.2f} km, Avg: {sum(dists)/len(dists):.2f} km")

# Name length / uniqueness
names = [r.get("name","") for r in records]
short_names = [n for n in names if len(n) < 10]
print(f"\nShort names (<10 chars): {len(short_names)}")
if short_names:
    for n in short_names[:20]:
        print(f"  '{n}'")

# Sample records with phone or website (high value)
high_value = [r for r in records if r.get("phone","").strip() or r.get("website","").strip()]
print(f"\nHigh value (phone or website): {len(high_value)}")
for r in high_value[:15]:
    print(f"  {r['name'][:45]:45s} | {r['category']:15s} | {r.get('phone',''):15s} | {r.get('website','')[:30]}")

# Contact by category
print("\nContact data by category:")
for cat in sorted(cats.keys()):
    subset = [r for r in records if r.get("category") == cat]
    wp = sum(1 for r in subset if r.get("phone","").strip())
    ws = sum(1 for r in subset if r.get("website","").strip())
    print(f"  {cat:20s}: {len(subset):3d} records, {wp:3d} with phone, {ws:3d} with website")
