"""
Export verified About-attributes from the pipeline into a JSON file the site
builder can consume.

Reads output-about/amenities.jsonl (records with `attributes` groups) and writes
a CID-keyed lookup:

    {
      "<googleCid>": {
        "listingId": "...",
        "sourceName": "...",
        "detectedGoogleName": "...",
        "capturedAt": "...",
        "attributeCount": 10,
        "attributes": [ { "group": "Service options", "items": ["Outdoor seating", ...] }, ... ]
      },
      ...
    }

Only records with at least one attribute group are included. Non-success
statuses are still included if they carry attribute data (e.g.
place_identity_mismatch where the detected place matched in substance).

Usage:
  python scripts/export_verified_attributes.py \
      --results amenity_pipeline/output-about/amenities.jsonl \
      --out paradisio_app/data/verified_attributes.json
"""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

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
        groups = rec.get("attributes") or []
        if not groups:
            continue
        cid = rec.get("googleCid")
        if not cid:
            continue
        items = []
        for g in groups:
            items.append({"group": g.get("group", ""), "items": g.get("attributes", [])})
        included += 1
        out[cid] = {
            "listingId": listing_id,
            "sourceName": rec.get("sourceName", ""),
            "detectedGoogleName": rec.get("detectedGoogleName"),
            "capturedAt": rec.get("capturedAt", ""),
            "attributeCount": sum(len(i["items"]) for i in items),
            "attributes": items,
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"records with results   : {len(latest)}")
    print(f"with attribute groups  : {included}")
    print(f"wrote                  : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
