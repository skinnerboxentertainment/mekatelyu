"""
Build the non-lodging listings queue for About-attribute extraction.

Keeps every record whose category is NOT lodging (restaurant, services, shopping,
tour_company, real_estate, transport, wellness) and has a numeric CID.

Usage:
  python scripts/build_nonlodging_queue.py \
      --csv pv_master_unified.csv \
      --out amenity_pipeline/output/nonlodging.jsonl
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

LODGING = {"hotel", "hostel", "vacation_rental"}


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
    parser.add_argument("--out", default=str(Path(__file__).parent.parent / "amenity_pipeline" / "output" / "nonlodging.jsonl"))
    args = parser.parse_args()

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8-sig")))
    records = []
    missing = []
    by_cat: dict[str, int] = {}

    for i, row in enumerate(rows):
        cat = (row.get("category") or "").strip().lower()
        if cat in LODGING:
            continue
        cid = (row.get("google_maps_cid") or "").strip()
        if not re.fullmatch(r"\d+", cid):
            missing.append((i, row.get("business_name", ""), cat))
            continue
        records.append({
            "listingId": slugify((row.get("business_name") or "").strip(), (row.get("area") or "").strip()),
            "name": (row.get("business_name") or "").strip(),
            "googleCid": cid,
            "category": cat,
            "area": (row.get("area") or "").strip(),
        })
        by_cat[cat] = by_cat.get(cat, 0) + 1

    records = dedup_slugs(records)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    print(f"non-lodging with CID : {len(records)}")
    print(f"without CID          : {len(missing)}")
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat:16s} {n}")
    print(f"wrote                : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
