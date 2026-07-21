"""Reconcile screenshot-backed CID discoveries and optionally apply safe matches.

Automatic application is deliberately narrow: the discovery must be classified
exact, its evidence image must exist and match its recorded digest, the target
master row must still have an empty CID, and the CID must not already occur in
the master dataset or another exact discovery.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
WORKSPACE = ROOT / "audit" / "maps-cid-discovery"
RESULTS = WORKSPACE / "unsigned-full" / "results.json"
REPORT = WORKSPACE / "FULL-SWEEP-REPORT.md"
DECISIONS = WORKSPACE / "reconciliation.csv"


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def evidence_valid(result: dict) -> tuple[bool, str]:
    screenshot = WORKSPACE / result.get("screenshot", "")
    if not screenshot.is_file():
        return False, "missing screenshot"
    digest = hashlib.sha256(screenshot.read_bytes()).hexdigest()
    if digest != result.get("screenshot_sha256"):
        return False, "screenshot hash mismatch"
    if not result.get("resolved_cid", "").isdigit():
        return False, "missing or invalid CID"
    return True, ""


def reconcile(apply: bool) -> int:
    master, fields = load_csv(MASTER)
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    if len(results) != 113:
        raise SystemExit(f"expected 113 results, found {len(results)}")

    by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    existing_by_cid: dict[str, list[str]] = defaultdict(list)
    for row in master:
        by_name[row["business_name"]].append(row)
        if row.get("google_maps_cid", "").strip():
            existing_by_cid[row["google_maps_cid"].strip()].append(row["business_name"])

    exact_counts = Counter(
        item["resolved_cid"] for item in results
        if item.get("classification") == "exact" and item.get("resolved_cid")
    )
    decisions: list[dict[str, str]] = []
    applied = 0
    for item in results:
        name = item["business_name"]
        cid = item.get("resolved_cid", "")
        classification = item.get("classification", "error")
        valid, evidence_issue = evidence_valid(item)
        target_rows = by_name.get(name, [])
        status = "review"
        reason = f"classifier={classification}"
        collision_names = existing_by_cid.get(cid, [])

        if not valid:
            status, reason = "rejected", evidence_issue
        elif len(target_rows) != 1:
            status, reason = "rejected", f"master row count={len(target_rows)}"
        elif target_rows[0].get("google_maps_cid", "").strip():
            status, reason = "rejected", "target CID is no longer empty"
        elif classification != "exact":
            status, reason = "review", f"classifier={classification}"
        elif collision_names:
            status, reason = "collision_review", "CID already assigned in master"
        elif exact_counts[cid] > 1:
            status, reason = "collision_review", "CID repeated in exact discovery set"
        else:
            status, reason = "safe", "exact + verified evidence + unique CID"
            if apply:
                target_rows[0]["google_maps_cid"] = cid
                applied += 1
                status = "applied"

        decisions.append({
            "business_name": name,
            "area": item.get("area", ""),
            "category": item.get("category", ""),
            "classification": classification,
            "observed_name": item.get("observed_name", ""),
            "identity_similarity": str(item.get("identity_similarity", "")),
            "resolved_cid": cid,
            "decision": status,
            "reason": reason,
            "existing_cid_businesses": " | ".join(collision_names),
            "screenshot": item.get("screenshot", ""),
            "screenshot_sha256": item.get("screenshot_sha256", ""),
            "final_url": item.get("final_url", ""),
        })

    decision_fields = list(decisions[0])
    write_csv(DECISIONS, decisions, decision_fields)
    if apply:
        write_csv(MASTER, master, fields)

    counts = Counter(row["decision"] for row in decisions)
    classes = Counter(row["classification"] for row in decisions)
    report = [
        "# Full Missing-CID Discovery Sweep",
        "",
        "## Outcome",
        "",
        f"- Records searched: {len(results)}",
        f"- Raw classifications: {classes['exact']} exact, {classes['probable']} probable, {classes['ambiguous']} ambiguous, {classes['no_result']} no result, {classes['error']} errors",
        f"- Safely applied to the local master: {counts['applied']}",
        f"- Safe but not applied (dry run): {counts['safe']}",
        f"- Existing/repeated CID collisions quarantined: {counts['collision_review']}",
        f"- Lower-confidence records held for review: {counts['review']}",
        f"- Rejected for failed invariants: {counts['rejected']}",
        "- Evidence integrity: every accepted candidate requires a present screenshot whose SHA-256 matches the capture manifest.",
        "",
        "## Guardrail",
        "",
        "Probable, ambiguous, duplicate-CID, and pre-existing-CID cases are never automatically written. A collision can indicate a legitimate alias/duplicate listing or a legacy CID assigned to the wrong business; both require identity reconciliation.",
        "",
        "## Review queues",
        "",
        "| Business | Class | Observed Maps name | CID | Decision | Collision / reason |",
        "|---|---|---|---|---|---|",
    ]
    for row in decisions:
        if row["decision"] not in {"applied", "safe"}:
            detail = row["existing_cid_businesses"] or row["reason"]
            values = [row["business_name"], row["classification"], row["observed_name"], row["resolved_cid"], row["decision"], detail]
            report.append("| " + " | ".join(value.replace("|", "/") for value in values) + " |")
    REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PASS: records={len(results)} applied={applied} decisions={dict(counts)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write safe exact matches into the master CSV")
    return reconcile(parser.parse_args().apply)


if __name__ == "__main__":
    raise SystemExit(main())
