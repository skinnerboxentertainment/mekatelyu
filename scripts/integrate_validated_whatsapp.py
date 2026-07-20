"""Integrate visually matched WhatsApp candidates into the local master CSV.

Only `phone_candidate` rows with an exact `match` result are eligible. The
operation is atomic and refuses stale, incomplete, or already-populated targets.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import tempfile
from pathlib import Path

from autovisual_whatsapp_checkifier import DEFAULT_WORKSPACE, ROOT, record_id


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", type=Path, default=ROOT / "pv_master_unified.csv")
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    master = load_csv(args.master)
    reconciliation = load_csv(args.workspace / "reconciliation.csv")
    candidates = {
        row["record_id"]: row
        for row in json.loads((args.workspace / "queues" / "candidates.json").read_text(encoding="utf-8"))
    }
    selected = {
        row["record_id"]: row for row in reconciliation
        if row["source_class"] == "phone_candidate" and row["identity_result"] == "match"
    }
    if len(selected) != 76:
        raise SystemExit(f"refusing integration: expected 76 strong matches, found {len(selected)}")

    master_by_id = {record_id(row.get("business_name", ""), row.get("area", "")): row for row in master}
    if len(master_by_id) != len(master):
        raise SystemExit("refusing integration: master record IDs are not unique")

    changes = []
    for identifier, evidence in selected.items():
        target = master_by_id.get(identifier)
        candidate = candidates.get(identifier)
        if not target or not candidate:
            raise SystemExit(f"refusing integration: missing master/candidate record {identifier}")
        if target.get("whatsapp", "").strip():
            raise SystemExit(f"refusing integration: target already has WhatsApp: {target['business_name']}")
        number = candidate["whatsapp_normalized"]
        if evidence["whatsapp_route"] != f"https://wa.me/{number.lstrip('+')}":
            raise SystemExit(f"refusing integration: route mismatch for {target['business_name']}")
        if candidate["source_class"] != "phone_candidate":
            raise SystemExit(f"refusing integration: wrong source class for {target['business_name']}")
        screenshot = args.workspace / evidence["screenshot_path"]
        if not screenshot.is_file() or hashlib.sha256(screenshot.read_bytes()).hexdigest() != evidence["screenshot_sha256"]:
            raise SystemExit(f"refusing integration: invalid visual evidence for {target['business_name']}")
        changes.append({
            "record_id": identifier, "business_name": target["business_name"], "area": target.get("area", ""),
            "old_whatsapp": target.get("whatsapp", ""), "new_whatsapp": number,
            "display_name": evidence["display_name"], "identity_result": evidence["identity_result"],
            "screenshot_path": evidence["screenshot_path"], "screenshot_sha256": evidence["screenshot_sha256"],
        })

    changes.sort(key=lambda row: row["business_name"].casefold())
    manifest = args.workspace / "integrated-strong-matches.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=changes[0].keys()); writer.writeheader(); writer.writerows(changes)

    if not args.apply:
        print(f"DRY RUN: {len(changes)} guarded WhatsApp additions are ready")
        print(f"Manifest: {manifest}")
        return 0

    selected_numbers = {row["record_id"]: row["new_whatsapp"] for row in changes}
    for row in master:
        identifier = record_id(row.get("business_name", ""), row.get("area", ""))
        if identifier in selected_numbers:
            row["whatsapp"] = selected_numbers[identifier]

    fieldnames = list(master[0].keys())
    descriptor, temporary_name = tempfile.mkstemp(prefix=".pv_master_unified.", suffix=".csv", dir=args.master.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(master)
        os.replace(temporary, args.master)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(f"APPLIED: {len(changes)} guarded WhatsApp additions")
    print(f"Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
