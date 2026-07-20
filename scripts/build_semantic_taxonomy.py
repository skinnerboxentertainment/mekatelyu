"""Build the local evidence-backed taxonomy index and review artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from paradisio_app.semantic_taxonomy import GROUP_LABELS, TAXONOMY_VERSION, classify_record

MASTER = ROOT / "pv_master_unified.csv"
PARSED = ROOT / "paradisio_app" / "data" / "maps_parsed_v3.json"
RAW_MAPS = ROOT / "docs" / "paradisio_app" / "data" / "maps_enrich_v2.json"
OUTPUT = ROOT / "paradisio_app" / "data" / "semantic_taxonomy.json"
AUDIT_DIR = ROOT / "audit" / "semantic-taxonomy"
RESOLUTIONS = AUDIT_DIR / "resolved-primary-categories.csv"
CID_DISCOVERY_RESULTS = ROOT / "audit" / "maps-cid-discovery" / "unsigned-full" / "results.json"
CID_DISCOVERY_DECISIONS = ROOT / "audit" / "maps-cid-discovery" / "reconciliation.csv"
CID_COLLISION_DECISIONS = ROOT / "audit" / "maps-cid-discovery" / "collision-decisions.csv"
CURRENT_DISCOVERY_RESULTS = ROOT / "audit" / "maps-cid-discovery" / "current-25" / "results.json"
CURRENT_DISCOVERY_DECISIONS = ROOT / "audit" / "maps-cid-discovery" / "remaining-evidence-decisions.csv"


def load_master() -> list[dict[str, str]]:
    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_accepted_discovery_text() -> dict[str, dict]:
    """Load only locally applied, screenshot-verified discovery captures."""
    if not CID_DISCOVERY_RESULTS.exists() or not CID_DISCOVERY_DECISIONS.exists():
        return {}
    results = json.loads(CID_DISCOVERY_RESULTS.read_text(encoding="utf-8"))
    by_name = {item["business_name"]: item for item in results}
    accepted_names = set()
    with CID_DISCOVERY_DECISIONS.open(encoding="utf-8", newline="") as handle:
        for decision in csv.DictReader(handle):
            if decision["decision"] == "applied":
                accepted_names.add(decision["business_name"])
    if CID_COLLISION_DECISIONS.exists():
        with CID_COLLISION_DECISIONS.open(encoding="utf-8", newline="") as handle:
            for decision in csv.DictReader(handle):
                if decision["disposition"] == "ownership_transferred":
                    accepted_names.add(decision["canonical_holder"])
    accepted = {}
    with CID_DISCOVERY_DECISIONS.open(encoding="utf-8", newline="") as handle:
        for decision in csv.DictReader(handle):
            if decision["business_name"] not in accepted_names:
                continue
            item = by_name.get(decision["business_name"])
            if not item or item.get("resolved_cid") != decision["resolved_cid"]:
                raise SystemExit(f"CID discovery evidence mismatch: {decision['business_name']}")
            screenshot = ROOT / "audit" / "maps-cid-discovery" / item["screenshot"]
            if not screenshot.is_file() or hashlib.sha256(screenshot.read_bytes()).hexdigest() != item["screenshot_sha256"]:
                raise SystemExit(f"CID discovery screenshot mismatch: {decision['business_name']}")
            accepted[decision["resolved_cid"]] = {
                "cid": decision["resolved_cid"],
                "business": decision["business_name"],
                "full_text": item.get("visible_text", ""),
                "text_length": item.get("visible_text_length", 0),
                "success": True,
                "source": "maps-cid-discovery/unsigned-full",
                "screenshot_sha256": item["screenshot_sha256"],
            }
    if CURRENT_DISCOVERY_RESULTS.exists() and CURRENT_DISCOVERY_DECISIONS.exists():
        current_results = {
            item["business_name"]: item
            for item in json.loads(CURRENT_DISCOVERY_RESULTS.read_text(encoding="utf-8"))
        }
        with CURRENT_DISCOVERY_DECISIONS.open(encoding="utf-8", newline="") as handle:
            for decision in csv.DictReader(handle):
                if decision["decision"] != "accepted":
                    continue
                item = current_results.get(decision["business_name"])
                if not item or item.get("resolved_cid") != decision["resolved_cid"]:
                    raise SystemExit(f"current CID evidence mismatch: {decision['business_name']}")
                screenshot = ROOT / "audit" / "maps-cid-discovery" / item["screenshot"]
                if not screenshot.is_file() or hashlib.sha256(screenshot.read_bytes()).hexdigest() != item["screenshot_sha256"]:
                    raise SystemExit(f"current CID screenshot mismatch: {decision['business_name']}")
                accepted[decision["resolved_cid"]] = {
                    "cid": decision["resolved_cid"], "business": decision["business_name"],
                    "full_text": item.get("visible_text", ""), "text_length": item.get("visible_text_length", 0),
                    "success": True, "source": "maps-cid-discovery/current-25",
                    "screenshot_sha256": item["screenshot_sha256"],
                }
    return accepted


def category_recommendation(item: dict) -> str:
    primary = item["primary_category"]
    tags = set(item["tags"])
    if primary == "restaurant" and "stay" in item["groups"]:
        if "hostel" in tags:
            return "Review primary → hostel"
        if "bed-and-breakfast" in tags or "hotel" in tags:
            return "Review primary → hotel"
        return "Review primary → vacation_rental"
    if primary == "restaurant" and "wellness" in item["groups"]:
        return "Review primary → wellness"
    if primary == "tour_company" and "transport" in item["groups"]:
        return "Review primary → transport"
    if primary in {"hotel", "hostel", "vacation_rental"} and "eat" in item["groups"]:
        return "Likely retain lodging primary; confirm Eat/Nightlife secondary visibility"
    return "Review evidence; retain current primary until resolved"


def main() -> int:
    rows = load_master()
    parsed_rows = json.loads(PARSED.read_text(encoding="utf-8"))
    parsed_by_cid = {str(item.get("cid", "")): item for item in parsed_rows if item.get("cid")}
    raw_rows = json.loads(RAW_MAPS.read_text(encoding="utf-8")) if RAW_MAPS.exists() else []
    raw_by_cid = {str(item.get("cid", "")): item for item in raw_rows if item.get("cid")}
    for cid, item in load_accepted_discovery_text().items():
        raw_by_cid.setdefault(cid, item)
    resolutions = {}
    if RESOLUTIONS.exists():
        with RESOLUTIONS.open(encoding="utf-8", newline="") as handle:
            resolutions = {(item["business_name"], item["area"]): item for item in csv.DictReader(handle)}

    records = []
    evidence_packets = []
    for row in rows:
        cid = row.get("google_maps_cid", "").strip()
        record = classify_record(row, parsed_by_cid.get(cid))
        resolution = resolutions.get((row.get("business_name", ""), row.get("area", "")))
        if resolution:
            record["resolution"] = {
                "disposition": resolution["disposition"],
                "resolved_category": resolution["resolved_category"],
                "rationale": resolution["rationale"],
            }
            if resolution["disposition"].startswith("retained_") and record["review_state"] == "review":
                record["review_state"] = resolution["disposition"]
        raw = raw_by_cid.get(cid, {})
        record["evidence_coverage"]["maps_full_text"] = bool(raw.get("full_text"))
        record["evidence_coverage"]["website"] = bool(row.get("website", "").strip())
        records.append(record)
        full_text = raw.get("full_text", "") or ""
        evidence_packets.append({
            "key": record["key"], "business_name": record["business_name"], "area": record["area"],
            "primary_category": record["primary_category"], "google_maps_cid": cid,
            "master_description": row.get("description_full", ""),
            "maps_parsed_fields": (parsed_by_cid.get(cid) or {}).get("fields", {}),
            "maps_full_text": full_text,
            "maps_full_text_length": len(full_text),
            "maps_full_text_sha256": hashlib.sha256(full_text.encode("utf-8")).hexdigest() if full_text else "",
            "maps_full_text_source": raw.get("source", "legacy-maps-enrichment") if full_text else "",
            "website": row.get("website", ""),
        })

    if len(records) != len(rows) or len({item["key"] for item in records}) != len(rows):
        raise SystemExit("semantic index does not preserve one unique record per master row")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "taxonomy_version": TAXONOMY_VERSION,
        "record_count": len(records),
        "groups": GROUP_LABELS,
        "records": {item["key"]: item for item in records},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    with (AUDIT_DIR / "evidence-packets.jsonl").open("w", encoding="utf-8", newline="") as handle:
        for packet in evidence_packets:
            handle.write(json.dumps(packet, ensure_ascii=False, separators=(",", ":")) + "\n")
    visibility_fields = ["key", "business_name", "area", "primary_category", "groups", "tags", "attributes",
                         "review_state", "conflicts", "master_description", "maps_parsed", "maps_full_text"]
    with (AUDIT_DIR / "visibility-matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=visibility_fields, lineterminator="\n")
        writer.writeheader()
        for item in records:
            writer.writerow({
                "key": item["key"], "business_name": item["business_name"], "area": item["area"],
                "primary_category": item["primary_category"], "groups": "|".join(item["groups"]),
                "tags": "|".join(item["tags"]), "attributes": "|".join(item["attributes"]),
                "review_state": item["review_state"],
                "conflicts": "|".join(item["conflicts"]),
                "master_description": item["evidence_coverage"]["master_description"],
                "maps_parsed": item["evidence_coverage"]["maps_parsed"],
                "maps_full_text": item["evidence_coverage"]["maps_full_text"],
            })

    review = [item for item in records if item["review_state"] == "review"]
    (AUDIT_DIR / "review-queue.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    review_report = [
        "# Semantic Primary-Category Review Queue", "",
        "These records already receive additive discovery visibility. This queue asks only whether",
        "their canonical primary category should change. No recommendation has been applied.", "",
        "| Business | Area | Current primary | Discovery groups | Recommendation | Evidence tags |",
        "|---|---|---|---|---|---|",
    ]
    for item in sorted(review, key=lambda value: value["business_name"].casefold()):
        cells = [item["business_name"], item["area"], item["primary_category"],
                 ", ".join(item["groups"]), category_recommendation(item), ", ".join(item["tags"])]
        review_report.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in cells) + " |")
    review_report.extend(["", "## Review rule", "",
                          "Confirm against the evidence packet and visible source identity before changing a primary category.",
                          "Mixed-use establishments may legitimately keep the current primary while retaining secondary groups.", ""])
    (AUDIT_DIR / "PRIMARY-CATEGORY-REVIEW.md").write_text("\n".join(review_report), encoding="utf-8")
    master_cids = {row.get("google_maps_cid", "").strip() for row in rows if row.get("google_maps_cid", "").strip()}
    unlinked = [item for cid, item in raw_by_cid.items() if cid not in master_cids]
    with (AUDIT_DIR / "unlinked-cid-captures.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["cid", "business", "text_length", "success"], lineterminator="\n")
        writer.writeheader()
        for item in sorted(unlinked, key=lambda value: str(value.get("business", "")).casefold()):
            writer.writerow({key: item.get(key, "") for key in writer.fieldnames})
    evidence_poor = [packet for packet in evidence_packets if not packet["maps_full_text"]]
    with (AUDIT_DIR / "evidence-poor-records.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["key", "business_name", "area", "primary_category", "google_maps_cid",
                  "website", "master_description_length"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for packet in evidence_poor:
            writer.writerow({
                "key": packet["key"], "business_name": packet["business_name"], "area": packet["area"],
                "primary_category": packet["primary_category"], "google_maps_cid": packet["google_maps_cid"],
                "website": packet["website"], "master_description_length": len(packet["master_description"]),
            })
    group_counts = Counter(group for item in records for group in item["groups"])
    tag_counts = Counter(tag for item in records for tag in item["tags"])
    attribute_counts = Counter(tag for item in records for tag in item["attributes"])
    evidence_counts = Counter()
    for item in records:
        for source, present in item["evidence_coverage"].items():
            if present:
                evidence_counts[source] += 1
    report = [
        "# Semantic Taxonomy Census", "", f"Taxonomy version: `{TAXONOMY_VERSION}`", "",
        f"- Master records indexed: {len(records)}", f"- Unique semantic keys: {len({r['key'] for r in records})}",
        f"- Records not awaiting review: {len(records) - len(review)}", f"- Unresolved review queue: {len(review)}", "",
        f"- Existing CID captures not linked to a current master CID: {len(unlinked)}",
        f"- Master records without linked full CID text: {len(evidence_poor)}", "",
        "## Evidence coverage", "",
    ]
    report.extend(f"- {source}: {evidence_counts[source]}/{len(records)}" for source in sorted(evidence_counts))
    report.extend(["", "## Discovery coverage", ""])
    report.extend(f"- {GROUP_LABELS[group]} (`{group}`): {group_counts[group]}" for group in GROUP_LABELS)
    report.extend(["", "## Most common specific tags", ""])
    report.extend(f"- `{tag}`: {count}" for tag, count in tag_counts.most_common())
    report.extend(["", "## Most common evidence-backed attributes", ""])
    report.extend(f"- `{tag}`: {count}" for tag, count in attribute_counts.most_common())
    report.extend(["", "## Safety interpretation", "",
                   "This index adds discovery groups, tags, and synonyms without changing canonical primary categories.",
                   "Unresolved conflicts remain in the review queue; reviewed mixed-use conflicts retain their recorded resolution.",
                   "No listing is removed by semantic indexing.", ""])
    (AUDIT_DIR / "CENSUS.md").write_text("\n".join(report), encoding="utf-8")
    print(f"PASS: indexed {len(records)} records; {len(review)} require review")
    print("Groups:", dict(group_counts))
    print(f"Output: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
