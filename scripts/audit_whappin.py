"""
Comprehensive Whappin audit — checks CSV source AND built release output.

Usage:
    python scripts/audit_whappin.py

Checks:
  CSV: category, area, coordinates, taxonomy, IG handles, URL integrity
  Release: rendered descriptions, WhatsApp sticky-bar consistency
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
DIRDATA_PATH = RELEASE_DIR / "static" / "directory-data.js"

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

IG_URL_PATTERN = re.compile(r"^https?://(www\.)?instagram\.com/")
VALID_IG_HANDLE = re.compile(r"^[A-Za-z0-9._]{1,30}$")

PLACEHOLDER_PATTERNS = [
    r'^[A-Z].+? (provides|offers) .+ in ',
    r'^[A-Z][a-zA-Z0-9\s\-\'\u00c0-\u024f]+ is (a|an) ',
    r' provides?\s+(hotel|accommodation|service)',
    r' offers?\s+(service)',
]


def load_release_lookup():
    """Build name->slug lookup from directory-data.js"""
    if not DIRDATA_PATH.exists():
        return {}
    content = DIRDATA_PATH.read_text(encoding="utf-8")
    m = re.search(r"const BUSINESSES=\[(.*?)\];", content, re.DOTALL)
    if not m:
        return {}
    businesses = json.loads("[" + m.group(1) + "]")
    return {b["name"].strip(): b["slug"] for b in businesses}


def audit():
    defects = []

    # Load taxonomy cache
    taxonomy = {}
    if TAXONOMY_PATH.exists():
        with open(TAXONOMY_PATH, encoding="utf-8") as f:
            taxonomy = json.load(f).get("records", {})

    # Load release slug lookup
    slug_map = load_release_lookup()

    # Build fuzzy match: normalize names for lookup
    def norm(s):
        return re.sub(r'[^a-z0-9]', '', s.lower())

    slug_map_norm = {norm(k): v for k, v in slug_map.items()}

    # Load CSV
    rows = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    contact_types_seen = defaultdict(list)
    wa_sticky_ok = 0
    wa_sticky_fail = 0

    for row in rows:
        name = row.get("business_name", "").strip()
        cid = row.get("google_maps_cid", "").strip()
        cat = row.get("category", "").strip().lower()
        area = row.get("area", "").strip()
        lat = row.get("latitude", "").strip()
        lng = row.get("longitude", "").strip()
        website = row.get("website", "").strip()
        ig_handle = row.get("instagram_handle", "").strip()
        desc = row.get("description_full", "").strip()
        status = row.get("operating_status", "").strip().lower()
        whatsapp = row.get("whatsapp", "").strip()

        # ===== CSV-LEVEL CHECKS =====

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

        # --- WEBSITE / URL INTEGRITY ---
        if website and IG_URL_PATTERN.match(website):
            defects.append({
                "business": name, "field": "website", "severity": "high",
                "issue": f"Website URL points to Instagram: {website}",
            })

        # --- IG HANDLE FORMAT ---
        if ig_handle and not VALID_IG_HANDLE.match(ig_handle):
            defects.append({
                "business": name, "field": "instagram_handle", "severity": "medium",
                "issue": f"Invalid IG handle format: {ig_handle}",
            })

        # --- STATUS ---
        if status == "needs_verification":
            defects.append({
                "business": name, "field": "status", "severity": "low",
                "issue": "Flagged needs_verification",
            })

        # --- TAXONOMY ---
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

        # ===== RELEASE-LEVEL CHECKS =====
        slug = slug_map.get(name) or slug_map_norm.get(norm(name))
        if not slug:
            continue

        page_path = RELEASE_DIR / "businesses" / f"{slug}.html"
        if not page_path.exists():
            continue

        html = page_path.read_text(encoding="utf-8")

        # --- DESCRIPTION ON SITE ---
        m = re.search(r'<div class="biz-desc">\s*<p>(.*?)</p>', html, re.DOTALL)
        if m:
            site_desc = m.group(1).strip()
            is_placeholder = False
            for pat in PLACEHOLDER_PATTERNS:
                if re.search(pat, site_desc, re.I):
                    is_placeholder = True
                    break
            if is_placeholder:
                defects.append({
                    "business": name, "field": "description", "severity": "medium",
                    "issue": f"Placeholder on site: '{site_desc[:120]}'",
                })
            elif len(site_desc) < 20:
                defects.append({
                    "business": name, "field": "description", "severity": "low",
                    "issue": f"Very short description on site ({len(site_desc)} chars): '{site_desc}'",
                })
        else:
            defects.append({
                "business": name, "field": "description", "severity": "medium",
                "issue": "No biz-desc found on page",
            })

        # --- WHATSAPP STICKY BAR CONSISTENCY ---
        if whatsapp:
            contact_types_seen["whatsapp"].append(name)
            if slug and page_path.exists():
                if 'data-plausible-channel="WhatsApp"' in html:
                    wa_sticky_ok += 1
                else:
                    wa_sticky_fail += 1
                    defects.append({
                        "business": name, "field": "contact", "severity": "high",
                        "issue": "WhatsApp in CSV but missing from sticky bar",
                    })

    # ===== SUMMARY =====
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
    print(f"  WhatsApp in CSV: {len(contact_types_seen['whatsapp'])}")
    print(f"  WhatsApp in sticky bar: {wa_sticky_ok}")
    print(f"  WhatsApp missing from sticky: {wa_sticky_fail}")
    print("=" * 70)

    return defects


if __name__ == "__main__":
    defects = audit()
    report_path = BASE_DIR / "audit" / "whappin_audit_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(defects, f, ensure_ascii=False, indent=2)
    print(f"\n  Full report written to {report_path}")
    sys.exit(0 if not [d for d in defects if d['severity'] == 'high'] else 1)
