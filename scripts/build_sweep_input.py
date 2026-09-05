"""
Turn the re-verification queue into an input file for the Maps pipeline.

This is what makes the freshness loop self-directing. Rather than re-crawling
736 records on a fixed rotation, each sweep asks the quality report which
records are actually closest to expiring and re-reads only those, worst first.
A small nightly batch therefore keeps the whole catalogue inside its policy
window without ever doing a full crawl.

Records with no Google Maps CID are skipped: there is nothing to re-read. They
stay visible in the quality report as unknown rather than being silently
dropped, because "we have no way to check this" is a fact about the catalogue
worth showing.

Usage:
  python scripts/build_sweep_input.py --limit 40 --out amenity_pipeline/sweep.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from paradisio_app import freshness  # noqa: E402
from paradisio_app.provenance import ProvenanceIndex  # noqa: E402

CSV_PATH = REPO / "pv_master_unified.csv"
DEFAULT_OUT = REPO / "amenity_pipeline" / "sweep.jsonl"


def slugify(name: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in name]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:80] or "listing"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=40,
                        help="how many records this sweep should re-read (default 40)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true", help="print the batch, write nothing")
    args = parser.parse_args()

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    index = ProvenanceIndex()
    scored = []
    for row in rows:
        cid = row.get("google_maps_cid", "").strip()
        if not cid:
            continue
        assessment = freshness.assess(row, index.capture_dates(cid))
        if assessment.worst == freshness.FRESH:
            continue
        scored.append((freshness.priority(assessment, row), row, cid, assessment))

    # Most urgent first; name breaks ties so a run is reproducible.
    scored.sort(key=lambda item: (-item[0], item[1].get("business_name", "")))
    batch = scored[: args.limit]

    lines = [
        json.dumps({
            "listingId": slugify(row.get("business_name", "")),
            "name": row.get("business_name", ""),
            "googleCid": cid,
        }, ensure_ascii=False)
        for _, row, cid, _ in batch
    ]

    print(f"{len(scored)} records need re-reading; this sweep takes {len(batch)}")
    if batch:
        worst = batch[0]
        print(f"  most urgent: {worst[1].get('business_name','')} "
              f"(priority {worst[0]}, stale: {', '.join(worst[3].stale_aspects) or 'none'})")
    if args.dry_run:
        for line in lines[:10]:
            print("  " + line)
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
