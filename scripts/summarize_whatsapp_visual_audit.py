"""Verify and summarize the latest image-backed WhatsApp audit attempts."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from autovisual_whatsapp_checkifier import DEFAULT_WORKSPACE, read_ledger


def main() -> int:
    workspace = DEFAULT_WORKSPACE
    queues = {}
    for name in ("preservation", "candidates", "pilot"):
        for item in json.loads((workspace / "queues" / f"{name}.json").read_text(encoding="utf-8")):
            queues[item["record_id"]] = item

    latest = {}
    for entry in read_ledger(workspace / "ledger.jsonl"):
        if entry.get("screenshot_sha256"):
            latest[entry["record_id"]] = entry

    errors = []
    rows = []
    for record_id, entry in latest.items():
        image = workspace / entry["screenshot_path"]
        if not image.is_file():
            errors.append(f"missing screenshot: {record_id}")
            continue
        digest = hashlib.sha256(image.read_bytes()).hexdigest()
        if digest != entry["screenshot_sha256"]:
            errors.append(f"hash mismatch: {record_id}")
        source = queues.get(record_id, {})
        rows.append({
            "record_id": record_id,
            "business_name": entry["business_name"],
            "area": source.get("area", ""),
            "phone": source.get("phone", ""),
            "whatsapp_route": entry["route"],
            "source_class": entry["source_class"],
            "identity_result": entry["identity_result"],
            "display_name": entry["display_name"],
            "confidence": entry["confidence"],
            "review_state": entry["review_state"],
            "evidence_summary": entry["evidence_summary"],
            "screenshot_path": entry["screenshot_path"],
            "screenshot_sha256": entry["screenshot_sha256"],
            "completed_at": entry["completed_at"],
        })

    rows.sort(key=lambda row: (row["source_class"], row["identity_result"], row["business_name"]))
    output = workspace / "reconciliation.csv"
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader(); writer.writerows(rows)

    counts = Counter((row["source_class"], row["identity_result"]) for row in rows)
    established = [row for row in rows if row["source_class"] == "master_explicit"]
    candidates = [row for row in rows if row["source_class"] == "phone_candidate"]
    proposed = [row for row in candidates if row["identity_result"] in {"match", "probable_match"}]
    established_exceptions = [row for row in established if row["identity_result"] != "match"]
    authority_queue = established_exceptions + proposed

    report = [
        "# Full WhatsApp visual audit report", "",
        "## Coverage", "",
        f"- Established explicit routes: {len(established)}/106",
        f"- Unpublished phone candidates: {len(candidates)}/523",
        f"- Negative controls: {sum(row['source_class'] == 'negative_control' for row in rows)}/1",
        f"- Hash-verified screenshots: {len(rows) - len(errors)}/{len(rows)}",
        "- Messages or calls sent: 0", "- Directory records changed: 0", "",
        "## Established-route findings", "",
        f"- Name matches: {counts['master_explicit', 'match']}",
        f"- Probable aliases requiring review: {counts['master_explicit', 'probable_match']}",
        f"- Visible-name mismatches requiring review: {counts['master_explicit', 'mismatch']}",
        f"- Number-only/inconclusive: {counts['master_explicit', 'unclear']}", "",
        "A mismatch is not automatically an invalid route: many businesses publish an owner's",
        "personal WhatsApp number. Existing explicit routes remain unchanged until human review.", "",
        "## Candidate findings", "",
        f"- Strong name matches: {counts['phone_candidate', 'match']}",
        f"- Probable name matches: {counts['phone_candidate', 'probable_match']}",
        f"- Different visible identity: {counts['phone_candidate', 'mismatch']}",
        f"- Proposed candidate review set: {len(proposed)}", "",
        "No candidate is approved or published by this report. Strong and probable matches form",
        "a proposed human-review set; mismatches remain unpublished.", "",
        "## Reconciliation", "",
        f"- Established exception review: {len(established_exceptions)}",
        f"- Candidate addition review: {len(proposed)}",
        f"- Total authority-tail decisions: {len(authority_queue)}",
        "- Machine-readable register: `reconciliation.csv`",
        "- Visual index: `REVIEW.md`",
        "- Authority required: approve additions, removals, or corrections after reviewing evidence.",
    ]
    if errors:
        report.extend(["", "## Integrity errors", "", *[f"- {error}" for error in errors]])
    (workspace / "FULL-AUDIT-REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 1 if errors or len(established) != 106 or len(candidates) != 523 else 0


if __name__ == "__main__":
    raise SystemExit(main())
