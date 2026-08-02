"""
Generate an amenity-pipeline listings file from pv_master_unified.csv.

Matches the slug scheme used by paradisio_app/build.py so extraction results can
be joined back to canonical records and the generated site.

Output: amenities-listings.jsonl  (one Listing JSON per row with a CID)
Usage:  python scripts/generate_listings.py [--csv pv_master_unified.csv] [--out amenities-listings.jsonl]
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def slugify(name: str, area: str) -> str:
    s = f"{name}-{area}"
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:80]


def dedup_slugs(businesses):
    seen = {}
    for biz in businesses:
        slug = biz["listingId"]
        if slug in seen:
            seen[slug] += 1
            biz["listingId"] = f"{slug}-{seen[slug]}"
        else:
            seen[slug] = 0
    return businesses


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default=str(Path(__file__).parent.parent / "pv_master_unified.csv"))
    parser.add_argument("--out", default=str(Path(__file__).parent.parent / "amenity_pipeline" / "amenities-listings.jsonl"))
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8-sig")))
    records = []
    missing = []
    seen_cids = {}

    for i, row in enumerate(rows):
        cid = (row.get("google_maps_cid") or "").strip()
        name = (row.get("business_name") or "").strip()
        area = (row.get("area") or "").strip()

        if not re.fullmatch(r"\d+", cid):
            missing.append((i, name, area, cid))
            continue

        records.append({
            "listingId": slugify(name, area),
            "name": name,
            "googleCid": cid,
            "category": (row.get("category") or "").strip(),
            "area": area,
        })

    records = dedup_slugs(records)

    for r in records:
        seen_cids[r["googleCid"]] = seen_cids.get(r["googleCid"], 0) + 1

    duplicates = {k: v for k, v in seen_cids.items() if v > 1}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"rows in csv      : {len(rows)}")
    print(f"with numeric CID : {len(records)}")
    print(f"without CID      : {len(missing)}")
    print(f"duplicate CIDs   : {len(duplicates)}")
    print(f"wrote            : {out}")

    if missing:
        print("\nrecords without CID:")
        for i, name, area, cid in missing:
            print(f"  [{i}] {name} ({area}) cid={cid!r}")
    if duplicates:
        print("\nCIDs appearing more than once:")
        for k, v in sorted(duplicates.items()):
            print(f"  {k} x{v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
