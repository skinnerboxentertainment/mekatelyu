"""
Build the lodging-only retry queue for the amenity pipeline.

From the full listings file, keep only records that are lodging (hotel / hostel /
vacation_rental) AND do not yet have a recovered amenity result. Non-lodging
categories are routed to `amenities_not_applicable` by the extractor and are out
of scope for the hotel-amenity extractor.

Usage:
  python scripts/build_lodging_retry.py \
      --listings amenities-listings.jsonl \
      --recovered output/amenities-recovered.jsonl \
      --out output/lodging-retry.jsonl
"""
import argparse
import json
from pathlib import Path

LODGING = {"hotel", "hostel", "vacation_rental"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listings", required=True)
    parser.add_argument("--recovered", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.listings, encoding="utf-8") as f:
        listings = [json.loads(line) for line in f if line.strip()]

    recovered_ids = set()
    with open(args.recovered, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                recovered_ids.add(json.loads(line)["listingId"])

    retry = [
        l
        for l in listings
        if l.get("category") in LODGING and l["listingId"] not in recovered_ids
    ]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for l in retry:
            f.write(json.dumps(l) + "\n")

    print(f"lodging listings     : {sum(1 for l in listings if l.get('category') in LODGING)}")
    print(f"recovered (any)      : {len(recovered_ids)}")
    print(f"lodging needing retry: {len(retry)}")
    print(f"wrote                : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
