"""Report on the health of the catalogue, and say what to re-check next.

A static site can still tell you how it is doing. This produces two things:

* a data-quality snapshot — coverage per field, freshness per aspect, and the
  size of the review backlog — written as a versioned artifact so a drop shows
  up as a diff rather than being discovered by a visitor;
* a prioritised re-verification queue, so the next batch of checking is chosen
  by what would cost someone a wasted journey rather than by whatever is at the
  top of the spreadsheet.

    python scripts/quality_report.py              # print the report
    python scripts/quality_report.py --write      # also write the JSON artifact
    python scripts/quality_report.py --queue 40   # show the next 40 to re-check

Read-only unless --write is passed, and even then it writes only the report.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from paradisio_app import freshness  # noqa: E402
from paradisio_app.provenance import ProvenanceIndex  # noqa: E402

CSV_PATH = REPO / "pv_master_unified.csv"
REPORT_PATH = REPO / "audit" / "quality" / "data-quality.json"

COVERAGE_FIELDS = [
    "google_maps_cid", "latitude", "phone", "whatsapp", "instagram_handle",
    "facebook_url", "website", "email", "booking_url", "tripadvisor_url",
]


def load_rows() -> list[dict]:
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def captures_for(index: ProvenanceIndex, cid: str) -> dict[str, str]:
    """Delegate to the provenance index rather than re-listing the stores.

    This used to hardcode amenities, attributes and hours. When operating status
    and identity gained capture dates, the report kept reading the old three and
    silently reported no improvement after a sweep that had in fact refreshed
    eleven records. One lookup, one place.
    """
    return index.capture_dates(cid)


def build_report(rows: list[dict], today: date) -> dict:
    index = ProvenanceIndex()
    coverage = {field: sum(1 for r in rows if (r.get(field) or "").strip()) for field in COVERAGE_FIELDS}
    states: Counter = Counter()
    aspect_states: dict[str, Counter] = {}
    queue = []

    for row in rows:
        assessment = freshness.assess(row, captures_for(index, row.get("google_maps_cid", "").strip()), today)
        states[assessment.worst] += 1
        for aspect, state in assessment.aspects.items():
            aspect_states.setdefault(aspect, Counter())[state] += 1
        score = freshness.priority(assessment, row)
        if score:
            queue.append({
                "business": row.get("business_name", ""),
                "cid": row.get("google_maps_cid", "").strip(),
                "priority": score,
                "stale": assessment.stale_aspects,
                "status": row.get("operating_status", "").strip(),
            })

    queue.sort(key=lambda item: (-item["priority"], item["business"]))
    return {
        "generated": today.isoformat(),
        "records": len(rows),
        "coverage": coverage,
        "coverage_pct": {k: round(100 * v / len(rows), 1) for k, v in coverage.items()},
        "freshness": dict(states),
        "freshness_by_aspect": {a: dict(c) for a, c in sorted(aspect_states.items())},
        "operating_status": dict(Counter((r.get("operating_status") or "blank").strip() for r in rows)),
        "review_backlog": sum(1 for r in rows if r.get("operating_status", "").strip() == "needs_verification"),
        "reverification_queue_size": len(queue),
        "reverification_queue": queue[:200],
    }


def print_report(report: dict, queue_size: int) -> None:
    print(f"Catalogue health — {report['generated']}   ({report['records']} records)\n")

    print("Coverage")
    for field, count in report["coverage"].items():
        pct = report["coverage_pct"][field]
        bar = "#" * int(pct / 4)
        print(f"   {field:20} {count:>4}  {pct:>5.1f}%  {bar}")

    print("\nFreshness — worst aspect per record")
    for state in (freshness.FRESH, freshness.AGING, freshness.STALE, freshness.UNKNOWN):
        count = report["freshness"].get(state, 0)
        print(f"   {state:9} {count:>4}  ({100 * count / report['records']:.1f}%)")

    print("\nFreshness by aspect")
    for aspect, counts in report["freshness_by_aspect"].items():
        total = sum(counts.values())
        stale = counts.get(freshness.STALE, 0) + counts.get(freshness.UNKNOWN, 0)
        print(f"   {aspect:18} {total:>4} assessed, {stale:>4} need re-checking")

    print(f"\nFlagged needs_verification: {report['review_backlog']}")
    print(f"Re-verification queue:      {report['reverification_queue_size']}")

    if queue_size:
        print(f"\nNext {queue_size} to re-check (most costly to get wrong first)")
        for item in report["reverification_queue"][:queue_size]:
            stale = ", ".join(item["stale"]) or "flagged"
            print(f"   {item['priority']:>4}  {item['business'][:48]:48} {stale}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="write the JSON artifact")
    parser.add_argument("--queue", type=int, default=0, help="show the next N to re-check")
    parser.add_argument("--today", default="", help="assess as at this date (YYYY-MM-DD)")
    args = parser.parse_args()

    today = freshness.parse_date(args.today) or date.today()
    report = build_report(load_rows(), today)
    print_report(report, args.queue)

    if args.write:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"\nwrote {REPORT_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
