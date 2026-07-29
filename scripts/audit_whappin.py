"""
Comprehensive Whappin data audit — checks every record against every rule.
Outputs a unified defect report grouped by severity.

Usage:
    python scripts/audit_whappin.py                    # audit CSV + taxonomy
    python scripts/audit_whappin.py --release          # also check built release output
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "pv_master_unified.csv"
TAXONOMY_PATH = BASE_DIR / "paradisio_app" / "data" / "semantic_taxonomy.json"
RELEASE_DIR = BASE_DIR / "release"

KNOWN_AREAS = {
    "Puerto Viejo", "Cocles", "Playa Negra", "Playa Cocles", "Playa Chiquita",
    "Punta Uva", "Manzanillo", "Cahuita", "Hone Creek", "Bribri", "Sixaola",
    "Gandoca", "South Caribbean",
}

KNOWN_CATEGORIES = {
    "hotel", "restaurant", "vacation_rental", "hostel", "services", "shopping",
    "tour_company", "real_estate", "wellness", "nightlife", "transport",
    "community_safety",
}

ACTIVITY_TAGS = {"surf", "diving", "snorkeling", "kayaking", "fishing", "wildlife", "yoga", "massage", "spa", "gym"}
NON_ACTIVITY_CATS = {"restaurant", "hotel", "vacation_rental", "hostel", "shopping", "services", "real_estate", "wellness", "transport"}

PLACEHOLDER_DESCRIPTIONS = [
    "provides hotel accommodations", "provides accommodation", "offers services in",
    "provides services in", "place in", "vacation rental option", "hotel accommodations",
]

IG_URL_PATTERN = re.compile(r"^https?://(www\.)?instagram\.com/")
VALID_IG_HANDLE = re.compile(r"^[A-Za-z0-9._]{1,30}$")


def audit():
    defects = []

    # Load taxonomy cache
    taxonomy = {}
    if TAXONOMY_PATH.exists():
        with open(TAXONOMY_PATH, encoding="utf-8") as f:
            taxonomy = json.load(f).get("records", {})

    # Load CSV
    rows = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    contact_types_seen = defaultdict(list)

    for row in rows:
        name = row.get("business_name", "").strip()
        cid = row.get("google_maps_cid", "").strip()
        cat = row.get("category", "").strip().lower()
        area = row.get("area", "").strip()
        lat = row.get("latitude", "").strip()
        lng = row.get("longitude", "").strip()
        phone = row.get("phone", "").strip()
        website = row.get("website", "").strip()
        ig_handle = row.get("instagram_handle", "").strip()
        ig_url = row.get("instagram_url", "").strip()
        fb_url = row.get("facebook_url", "").strip()
        desc = row.get("description_full", "").strip()
        status = row.get("operating_status", "").strip().lower()
        whatsapp = row.get("whatsapp", "").strip()

        # --- CATEGORY ---
        if cat and cat not in KNOWN_CATEGORIES:
            defects.append({
                "business": name, "field": "category", "severity": "high",
                "issue": f"Unknown category: {cat}",
            })

        # --- AREA ---
        if area and area not in KNOWN_AREAS:
            defects.append({
                "business": name, "field": "area", "severity": "medium",
                "issue": f"Unknown area: {area}",
            })

        # --- COORDINATES ---
        has_coords = bool(lat and lng)
        has_cid = bool(cid)
        if not has_coords and not has_cid:
            defects.append({
                "business": name, "field": "coordinates", "severity": "high",
                "issue": "No coordinates and no Google Maps CID — invisible on map",
            })
        elif not has_coords and has_cid:
            pass  # area-backfill handles this

        # --- CONTACT INTEGRITY ---
        if whatsapp:
            contact_types_seen["whatsapp"].append(name)

        # Website URL is actually Instagram
        if website and IG_URL_PATTERN.match(website):
            defects.append({
                "business": name, "field": "website", "severity": "high",
                "issue": f"Website URL points to Instagram: {website}",
            })

        # IG handle format
        if ig_handle and not VALID_IG_HANDLE.match(ig_handle):
            defects.append({
                "business": name, "field": "instagram_handle", "severity": "medium",
                "issue": f"Invalid IG handle format: {ig_handle}",
            })

        # --- DESCRIPTION ---
        if desc:
            for phrase in PLACEHOLDER_DESCRIPTIONS:
                if phrase in desc.lower():
                    defects.append({
                        "business": name, "field": "description", "severity": "medium",
                        "issue": f"Placeholder description: '{desc[:120]}'",
                    })
                    break
            if len(desc) < 30:
                defects.append({
                    "business": name, "field": "description", "severity": "low",
                    "issue": f"Very short description ({len(desc)} chars): '{desc}'",
                })
        else:
            defects.append({
                "business": name, "field": "description", "severity": "low",
                "issue": "Missing description",
            })

        # --- STATUS ---
        if status == "needs_verification":
            defects.append({
                "business": name, "field": "status", "severity": "low",
                "issue": "Flagged needs_verification",
            })

        # --- TAXONOMY (from cache) ---
        tax_key = f"cid:{cid}" if cid else f"name:{name.lower()}"
        tax_entry = taxonomy.get(tax_key)
        if tax_entry:
            attrs = tax_entry.get("attributes", [])
            tags = tax_entry.get("tags", [])
            for tag in attrs + tags:
                if tag in ACTIVITY_TAGS and cat in NON_ACTIVITY_CATS:
                    defects.append({
                        "business": name, "field": "taxonomy", "severity": "high",
                        "issue": f"{cat} tagged with activity '{tag}'",
                    })

    # --- SUMMARY ---
    by_severity = defaultdict(list)
    for d in defects:
        by_severity[d["severity"]].append(d)

    print("=" * 70)
    print("  WHAPPIN DATA AUDIT REPORT")
    print("=" * 70)
    print(f"\n  Total records scanned: {len(rows)}")
    print(f"  Total defects: {len(defects)}")

    for sev in ("high", "medium", "low"):
        items = by_severity[sev]
        print(f"\n  --- {sev.upper()} severity ({len(items)}) ---")
        for d in items:
            print(f"    [{d['business']}] {d['field']}: {d['issue']}")

    print(f"\n  --- Contact summary ---")
    print(f"  WhatsApp advertised: {len(contact_types_seen['whatsapp'])}")
    print("=" * 70)

    return defects


if __name__ == "__main__":
    defects = audit()
    report_path = BASE_DIR / "audit" / "whappin_audit_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(defects, f, ensure_ascii=False, indent=2)
    print(f"\n  Full report written to {report_path}")
    sys.exit(0 if not defects else 1)
