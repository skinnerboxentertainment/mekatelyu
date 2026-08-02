"""
Export verified operating-hours data into a separate days file the site builder
can consume.

Reads output-hours/amenities.jsonl (records with `weeklyHours`) and writes a
CID-keyed JSON:

    {
      "<googleCid>": {
        "listingId": "...",
        "sourceName": "...",
        "detectedGoogleName": "...",
        "capturedAt": "...",
        "timezone": "America/Costa_Rica",
        "completeness": "complete" | "partial",
        "weeklyHours": {
          "monday": { "closed": false, "open24Hours": false, "periods": [{"opens":"10:00","closes":"22:00","closesNextDay":false}] },
          "tuesday": { "closed": true, "open24Hours": false, "periods": [] },
          ...
        },
        "specialHours": [ { "displayDay": "...", "raw": "..." } ]
      }
    }

Only records with at least one parsed weekday are included. Partial schedules
are preserved (with completeness flagged) rather than fabricated.

Usage:
  python scripts/export_verified_hours.py \
      --results amenity_pipeline/output-hours/amenities.jsonl \
      --out paradisio_app/data/verified_hours.json
"""
import argparse
import json
import re
from pathlib import Path

WEEKDAYS = [
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
]


def clean_display_day(value):
    """Reduce a raw displayDay to the weekday plus any holiday parenthetical."""
    if not value:
        return value
    m = re.match(r"^(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)(\([^)]*\))?", value, re.I)
    return m.group(0) if m else value


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
        weekly = rec.get("weeklyHours") or {}
        if not weekly:
            continue
        # Clean raw displayDay values (strip the repeated row/cell text).
        cleaned = {}
        for day, sched in weekly.items():
            entry = dict(sched)
            if isinstance(entry.get("displayDay"), str):
                entry["displayDay"] = clean_display_day(entry["displayDay"])
            cleaned[day] = entry
        cid = rec.get("googleCid")
        if not cid:
            continue
        included += 1
        out[cid] = {
            "listingId": listing_id,
            "sourceName": rec.get("sourceName", ""),
            "detectedGoogleName": rec.get("detectedGoogleName"),
            "capturedAt": rec.get("capturedAt", ""),
            "timezone": "America/Costa_Rica",
            "completeness": rec.get("hoursCompleteness", "partial"),
            "weeklyHours": cleaned,
            "specialHours": rec.get("specialHours") or [],
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"records with results : {len(latest)}")
    print(f"with weekly hours    : {included}")
    print(f"wrote                : {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
