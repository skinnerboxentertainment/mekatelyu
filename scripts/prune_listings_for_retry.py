"""
Build a focused amenities listings file containing only records that have NOT
yet produced amenities, so a re-run with throttle backoff targets just them.

Reads the latest per-listing result from an amenities.jsonl and writes a new
listings JSONL (compatible with the pipeline) for every record with 0 amenities.

Usage:
  python scripts/prune_listings_for_retry.py \
      --listings amenity_pipeline/amenities-listings.jsonl \
      --results amenity_pipeline/output/amenities.jsonl \
      --out amenity_pipeline/retry-listings.jsonl
"""
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listings", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.listings, encoding="utf-8") as f:
        listings = [json.loads(line) for line in f if line.strip()]

    # Latest result per listingId.
    latest: dict[str, dict] = {}
    with open(args.results, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            cur = latest.get(rec["listingId"])
            if cur is None or rec.get("capturedAt", "") >= cur.get("capturedAt", ""):
                latest[rec["listingId"]] = rec

    retry = []
    for listing in listings:
        rec = latest.get(listing["listingId"])
        if rec is None or rec.get("amenityCount", 0) == 0:
            retry.append(listing)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for listing in retry:
            f.write(json.dumps(listing) + "\n")

    print(f"total listings    : {len(listings)}")
    print(f"have amenities    : {len(listings) - len(retry)}")
    print(f"need retry        : {len(retry)}")
    print(f"wrote             : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
