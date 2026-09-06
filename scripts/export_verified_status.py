"""
Export verified operating status and place identity from a Maps pipeline run.

The pipeline already determines both of these on every single record it visits —
`operatingStatus` (open / permanently_closed / temporarily_closed / unknown) and
`detectedGoogleName`, the name Google actually shows for the CID — and then
discards them, because the exporters written so far only cared about amenities,
attributes and hours.

That omission is why 574 of 736 records report a stale operating status and 306
report a stale identity: those two aspects had no capture date of their own, so
the freshness engine fell back to the CSV's `verified_date`, a column nothing
has written since the original 2026-07-04 crawl. Publishing this sidecar gives
them a real age and makes them refreshable, which is what P1 needs in order to
be measurable at all.

This writes evidence, not corrections. It records what Google said and when;
changing a business's `operating_status` in the canonical CSV is a data mutation
and goes through `scripts/apply_status_corrections.py`, under the usual dry-run
and archive discipline.

Usage:
  python scripts/export_verified_status.py \
      --results amenity_pipeline/output/amenities.jsonl \
      --out paradisio_app/data/verified_status.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS = REPO / "amenity_pipeline" / "output" / "amenities.jsonl"
DEFAULT_OUT = REPO / "paradisio_app" / "data" / "verified_status.json"

# Statuses the pipeline can assert about a place. Anything outside this set is
# treated as no assertion rather than coerced, so a pipeline change cannot
# quietly introduce a status the site does not understand.
KNOWN_STATUSES = frozenset({"open", "permanently_closed", "temporarily_closed", "unknown"})

# Page-level outcomes that mean "we reached the right place and read it". Any
# other status means we did not get a clean look, so nothing is recorded — a
# failed check must never masquerade as a fresh one.
CONCLUSIVE = frozenset({
    # Read cleanly, section present.
    "success_expanded",
    "success_inline",
    "success_attributes",
    "success_hours",
    # The place told us it is shut. That is a reading, not a failure.
    "business_closed",
    "business_permanently_closed",
    "business_temporarily_closed",
    # The page loaded and we identified the place, but the amenities, attributes
    # or hours section was absent or would not parse. Irrelevant here: we are
    # capturing operating status and identity, both of which were read. Measured
    # on 2026-09-05, treating these as failures threw away 6 of 10 usable reads.
    "amenities_not_applicable",
    "amenities_not_exposed",
    "attributes_not_exposed",
    "hours_not_exposed",
    "hours_expansion_failed",
    "hours_parse_failed",
})


def read_records(path: Path) -> list[dict]:
    """Read a JSONL results file, skipping blank and unparseable lines."""
    records = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def build_index(records: list[dict]) -> tuple[dict, dict]:
    """Reduce pipeline records to a CID-keyed status/identity store.

    Returns the store plus a counts dict for the run summary. Later records win,
    so re-running the pipeline over a subset updates only what it re-read.
    """
    store: dict[str, dict] = {}
    counts = {
        "records": len(records),
        "kept": 0,
        "no_cid": 0,
        "inconclusive": 0,
        "identity_mismatch": 0,
    }

    for record in records:
        cid = str(record.get("googleCid") or "").strip()
        if not cid:
            counts["no_cid"] += 1
            continue

        page_status = record.get("status") or ""
        if page_status not in CONCLUSIVE:
            # Consent walls, CAPTCHAs, navigation failures and identity
            # mismatches all land here. None of them tell us the business is
            # fine; they tell us we could not look.
            counts["inconclusive"] += 1
            if page_status == "place_identity_mismatch":
                counts["identity_mismatch"] += 1
            continue

        captured = str(record.get("capturedAt") or "").strip()
        if not captured:
            counts["inconclusive"] += 1
            continue

        operating = record.get("operatingStatus")
        if operating not in KNOWN_STATUSES:
            operating = None
        detected = record.get("detectedGoogleName")

        # Belt and braces: a page status in the conclusive set is not on its own
        # proof we read anything. Without a name or a status there is nothing to
        # date, and dating an aspect we did not read is the one outcome worse
        # than leaving it stale.
        if not detected and operating is None:
            counts["inconclusive"] += 1
            continue

        store[cid] = {
            "listingId": record.get("listingId", ""),
            "sourceName": record.get("sourceName", ""),
            "detectedGoogleName": detected,
            "capturedAt": captured,
            "operatingStatus": operating,
            "pageStatus": page_status,
            "extractorVersion": record.get("extractorVersion", ""),
        }
        counts["kept"] += 1

    return store, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--merge", action="store_true",
                        help="merge into the existing store instead of replacing it, "
                             "so a partial sweep does not discard earlier captures")
    args = parser.parse_args()

    if not args.results.exists():
        print(f"no results file at {args.results}")
        print("run the Maps pipeline first, or pass --results")
        return 1

    records = read_records(args.results)
    store, counts = build_index(records)

    if args.merge and args.out.exists():
        existing = json.loads(args.out.read_text(encoding="utf-8"))
        merged = dict(existing)
        merged.update(store)
        store = merged

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(store, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    closed = sum(1 for v in store.values() if v["operatingStatus"] in {"permanently_closed", "temporarily_closed"})
    print(f"read {counts['records']} pipeline records")
    print(f"  kept              {counts['kept']}")
    print(f"  no CID            {counts['no_cid']}")
    print(f"  inconclusive      {counts['inconclusive']} (of which identity mismatch: {counts['identity_mismatch']})")
    print(f"wrote {len(store)} CIDs to {args.out}")
    print(f"  reporting closed  {closed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
