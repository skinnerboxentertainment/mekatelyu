"""
Export verified amenity data from the amenity pipeline into a JSON file the
site builder can consume.

Reads output/amenities.jsonl (one record per listing, with per-amenity
`available` booleans) and writes a CID-keyed lookup:

    {
      "<googleCid>": {
        "listingId": "...",
        "sourceName": "...",
        "capturedAt": "...",
        "extractorVersion": "...",
        "amenities": [ { "key": "free_wifi", "name": "Free Wi-Fi", "available": true }, ... ],
        "availableNames": ["Free Wi-Fi", ...],
        "unavailableNames": ["Pool", ...]
      },
      ...
    }

Only records with at least one `available: true` amenity are included (the rest
are businesses with no offered amenities, which we intentionally show nothing
for rather than injecting defaults).

Usage:
  python scripts/export_verified_amenities.py \
      --results amenity_pipeline/output/amenities.jsonl \
      --listings amenity_pipeline/amenities-listings.jsonl \
      --out paradisio_app/data/verified_amenities.json
"""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True)
    parser.add_argument("--listings", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.listings, encoding="utf-8") as f:
        listings = [json.loads(line) for line in f if line.strip()]
    by_id = {l["listingId"]: l for l in listings}

    latest: dict[str, dict] = {}
    with open(args.results, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            cur = latest.get(rec["listingId"])
            if cur is None or rec.get("capturedAt", "") >= cur.get("capturedAt", ""):
                latest[rec["listingId"]] = rec

    out: dict[str, dict] = {}
    included = 0
    for listing_id, rec in latest.items():
        amenities = rec.get("amenities", [])
        available = [a for a in amenities if a.get("available") is True]
        if not available:
            continue
        listing = by_id.get(listing_id)
        cid = (listing or {}).get("googleCid") or rec.get("googleCid")
        if not cid:
            continue
        included += 1
        out[cid] = {
            "listingId": listing_id,
            "sourceName": (listing or {}).get("name", rec.get("sourceName", "")),
            "capturedAt": rec.get("capturedAt", ""),
            "extractorVersion": rec.get("extractorVersion", ""),
            "amenities": amenities,
            "availableNames": [a["name"] for a in available],
            "unavailableNames": [a["name"] for a in amenities if a.get("available") is False],
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"listings with results : {len(latest)}")
    print(f"with available amenities: {included}")
    print(f"wrote                 : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
