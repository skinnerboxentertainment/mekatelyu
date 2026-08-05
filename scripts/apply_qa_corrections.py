"""Apply QA-triage corrections to pv_master_unified.csv from the qa-triage manifests.

Manifests (audit/qa-triage/):
  category-corrections.csv   business_name,area,old_category,new_category
  area-corrections.csv       business_name,old_area,new_area
  removals.csv               (NOT applied unless --apply-removals)

The script validates every precondition before writing and refuses to apply
partially. Removals are intentionally off by default so the owner can review.

Usage:
  python scripts/apply_qa_corrections.py                 # dry run
  python scripts/apply_qa_corrections.py --apply          # apply categories + areas
  python scripts/apply_qa_corrections.py --apply-removals # also delete removal rows
"""

from __future__ import annotations

import argparse
import csv
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
TRIAGE = ROOT / "audit" / "qa-triage"
CATEGORY_MANIFEST = TRIAGE / "category-corrections.csv"
AREA_MANIFEST = TRIAGE / "area-corrections.csv"
REMOVAL_MANIFEST = TRIAGE / "removals.csv"
CONTACT_MANIFEST = TRIAGE / "contact-corrections.csv"
DESCRIPTION_MANIFEST = TRIAGE / "description-corrections.csv"


def clean_tripadvisor(raw: str) -> str:
    """Strip the affiliate-wrapper prefix to leave a clean TripAdvisor URL."""
    value = (raw or "").strip()
    marker = "https://www.tripadvisor.com/"
    idx = value.find(marker)
    if idx >= 0:
        return value[idx:]
    return value


def read_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row.get("business_name")]


def apply_to_master() -> None:
    rows = []
    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames

    categories = read_manifest(CATEGORY_MANIFEST)
    areas = read_manifest(AREA_MANIFEST)
    removals = read_manifest(REMOVAL_MANIFEST)

    by_name = {}
    for row in rows:
        by_name.setdefault(row["business_name"].strip(), []).append(row)

    audit = []
    changed = 0

    def verify_single(targets, name, expected_field, expected_value):
        found = [t for t in targets if t[expected_field] == expected_value]
        if len(found) != 1:
            raise SystemExit(
                f"refusing correction for {name}: expected exactly one row with "
                f"{expected_field}={expected_value!r}, found {len(found)}"
            )
        return found[0]

    def lookup(name):
        targets = by_name.get(name, [])
        if len(targets) != 1:
            raise SystemExit(f"refusing correction for {name}: expected exactly one row by name, found {len(targets)}")
        return targets[0]

    for decision in categories:
        name = decision["business_name"].strip()
        row = lookup(name)
        new_cat = decision["new_category"].strip()
        if row["category"] == new_cat:
            audit.append(f"[category] {name} ({row['area']}): already {new_cat} (ticket {decision['ticket']})")
            continue
        if row["category"] != decision["old_category"].strip():
            raise SystemExit(
                f"refusing category change for {name}: expected current "
                f"{decision['old_category']!r}, found {row['category']!r}"
            )
        audit.append(
            f"[category] {name} ({row['area']}): {row['category']} -> {new_cat} (ticket {decision['ticket']})"
        )
        row["category"] = new_cat
        changed += 1

    for decision in areas:
        name = decision["business_name"].strip()
        row = lookup(name)
        new_area = decision["new_area"].strip()
        if row["area"] == new_area:
            audit.append(f"[area] {name}: already {new_area} (ticket {decision['ticket']})")
            continue
        if row["area"] != decision["old_area"].strip():
            raise SystemExit(
                f"refusing area change for {name}: expected current "
                f"{decision['old_area']!r}, found {row['area']!r}"
            )
        audit.append(f"[area] {name}: {row['area']} -> {new_area} (ticket {decision['ticket']})")
        row["area"] = new_area
        changed += 1

    for decision in read_manifest(CONTACT_MANIFEST):
        name = decision["business_name"].strip()
        row = lookup(name)
        op = decision["op"].strip()
        old = decision["old"].strip()
        new = decision["new"].strip()
        tag = f"(ticket {decision['ticket']})"
        if op == "ig_replace":
            if row["instagram_handle"] == new:
                audit.append(f"[ig] {name}: already @{new} {tag}")
                continue
            if row["instagram_handle"] != old:
                raise SystemExit(f"refusing ig_replace for {name}: expected handle {old!r}, found {row['instagram_handle']!r}")
            row["instagram_handle"] = new
            row["instagram_url"] = f"https://www.instagram.com/{new}/"
            row["instagram_confidence"] = "verified"
            row["ig_verified"] = "true"
            audit.append(f"[ig] {name}: @{old} -> @{new} {tag}")
            changed += 1
        elif op == "ig_clear":
            if not row["instagram_handle"]:
                audit.append(f"[ig] {name}: already cleared {tag}")
                continue
            if old and row["instagram_handle"] != old:
                raise SystemExit(f"refusing ig_clear for {name}: expected handle {old!r}, found {row['instagram_handle']!r}")
            audit.append(f"[ig] {name}: @{row['instagram_handle']} removed {tag}")
            row["instagram_handle"] = ""
            row["instagram_url"] = ""
            row["instagram_confidence"] = "removed"
            changed += 1
        elif op == "fb_clear":
            if not row["facebook_url"]:
                audit.append(f"[fb] {name}: already cleared {tag}")
                continue
            if old and row["facebook_url"] != old:
                raise SystemExit(f"refusing fb_clear for {name}: expected {old!r}, found {row['facebook_url']!r}")
            audit.append(f"[fb] {name}: removed {tag}")
            row["facebook_url"] = ""
            changed += 1
        elif op == "web_to_ta":
            if not row["website"] and clean_tripadvisor(row["tripadvisor_url"]) == clean_tripadvisor(old):
                audit.append(f"[web] {name}: already moved to tripadvisor_url {tag}")
                continue
            if row["website"] != old:
                raise SystemExit(f"refusing web_to_ta for {name}: expected website {old!r}, found {row['website']!r}")
            audit.append(f"[web] {name}: website -> tripadvisor_url {tag}")
            row["tripadvisor_url"] = clean_tripadvisor(row["website"])
            row["website"] = ""
            changed += 1
        elif op == "ta_clean":
            if row["tripadvisor_url"] == new:
                audit.append(f"[ta] {name}: already clean {tag}")
                continue
            if row["tripadvisor_url"] != old:
                raise SystemExit(f"refusing ta_clean for {name}: expected {old!r}, found {row['tripadvisor_url']!r}")
            if clean_tripadvisor(old) != new:
                raise SystemExit(f"refusing ta_clean for {name}: cleaned target mismatch")
            audit.append(f"[ta] {name}: affiliate URL cleaned {tag}")
            row["tripadvisor_url"] = new
            changed += 1
        elif op == "status_set":
            if row["operating_status"] == new:
                audit.append(f"[status] {name}: already {new} {tag}")
                continue
            if row["operating_status"] != old:
                raise SystemExit(f"refusing status_set for {name}: expected {old!r}, found {row['operating_status']!r}")
            audit.append(f"[status] {name}: {row['operating_status']} -> {new} {tag}")
            row["operating_status"] = new
            changed += 1
        else:
            raise SystemExit(f"unknown contact op: {op}")

    for decision in read_manifest(DESCRIPTION_MANIFEST):
        name = decision["business_name"].strip()
        row = lookup(name)
        if "is a restaurant" in row["description_full"].lower():
            audit.append(f"[desc] {name}: stale restaurant description replaced {tag}")
            row["description_full"] = decision["new"].strip()
            changed += 1
        else:
            audit.append(f"[desc] {name}: description already clean {tag}")

    if removals and not REMOVE_FLAG:
        print(f"NOTE: {len(removals)} removal(s) staged but not applied (no --apply-removals).")
    if REMOVE_FLAG:
        remove_names = {r["business_name"].strip() for r in removals}
        before = len(rows)
        rows = [row for row in rows if row["business_name"].strip() not in remove_names]
        removed = before - len(rows)
        audit.append(f"[removal] removed {removed} non-business reference rows")
        changed += removed

    print(f"\nDRY RUN SUMMARY: {len(audit)} changes would apply")
    for line in audit:
        print(f"  {line}")
    if not APPLY:
        return

    descriptor, temporary_name = tempfile.mkstemp(prefix=".pv_master_unified.", suffix=".csv", dir=MASTER.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, MASTER)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(f"\nAPPLIED: {changed} changes written to {MASTER.name}")
    for line in audit:
        print(f"  {line}")


APPLY = False
REMOVE_FLAG = False


def main() -> int:
    global APPLY, REMOVE_FLAG
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--apply-removals", action="store_true")
    args = parser.parse_args()
    APPLY = args.apply
    REMOVE_FLAG = args.apply_removals
    apply_to_master()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
