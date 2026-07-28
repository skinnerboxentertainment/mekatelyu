"""
Audit amenity data in Maps enrich pipeline.

Reads the active enrich source (maps_parsed_v3.json), applies proposed
cleaning rules, and reports what would change — WITHOUT modifying any files.

Usage:
    python scripts/audit_amenities.py
"""

import json
import re
import csv
import sys
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
ENRICH_PATH = BASE_DIR / "paradisio_app" / "data" / "maps_parsed_v3.json"
CSV_PATH = BASE_DIR / "pv_master_unified.csv"
REPORT_PATH = BASE_DIR / "audit" / "amenity_audit_report.csv"

VALID_AMENITY_PATTERNS = [
    r"^wi[-\s]?fi($|\s)",
    r"^wifi($|\s)",
    r"^internet($|\s)",
    r"^incluye\s",
    r"^estacionamiento\s",
    r"^aire\s*acondicionado",
    r"^air\s*conditioning",
    r"^piscina",
    r"^pool($|\s)",
    r"^desayuno",
    r"^breakfast",
    r"^gimnasio($|\s)",
    r"^gym($|\s)",
    r"^(se\s)?permite[n]?\s*mascotas",
    r"^aceptan?\s*mascotas",
    r"^pet\s*friendly",
    r"^accesibl",
    r"^wheelchair",
    r"^transporte\s*desde",
    r"^airport\s*shuttle",
    r"^cocina($|\s)",
    r"^kitchen($|\s)",
    r"^bar($|\s)",
    r"^spa($|\s)",
    r"^libre\s*de\s*humo",
    r"^smoke[-\s]?free",
    r"^centro\s*de\s*negocios",
    r"^business\s*center",
    r"^(bed\s*&\s*breakfast|b\s*&\s*b)$",
    r"^espacio($|\s)",
    r"^outdoor\s*space",
    r"^terraza($|\s)",
    r"^terrace($|\s)",
    r"^restobar($|\s)",
    r"^acceso\s*a\s*la\s*playa",
    r"^beach\s*access",
    r"^pago\s*sin\s*contacto",
    r"^contactless\s*payment",
]

VALID_AMENITY_COMPILED = [re.compile(p, re.IGNORECASE) for p in VALID_AMENITY_PATTERNS]

NOISE_PATTERNS = [
    r"^\d{5}$",
    r"\.(com|cr|net|org)$",
    r"^http",
    r"^\w+\.\w+$",
]

NOISE_COMPILED = [re.compile(p, re.IGNORECASE) for p in NOISE_PATTERNS]

NOISE_WORDS = {
    "cahuita", "limón", "limon", "puerto viejo", "manzanillo", "cocles",
    "playa negra", "playa cocles", "punta uva", "bribri", "sixaola",
    "gandoca", "hone creek", "costa rica",
}


def is_valid_amenity(text):
    text_stripped = text.strip()
    if not text_stripped:
        return False
    text_lower = text_stripped.lower()
    if text_lower in NOISE_WORDS:
        return False
    for pattern in NOISE_COMPILED:
        if pattern.search(text_stripped):
            return False
    for pattern in VALID_AMENITY_COMPILED:
        if pattern.search(text_stripped):
            return True
    return False


def parse_amenities(raw_value):
    if not raw_value:
        return []
    if isinstance(raw_value, list):
        return [str(p).strip() for p in raw_value if p and str(p).strip()]
    parts = re.split(r'[,;\n]+', str(raw_value))
    return [p.strip() for p in parts if p.strip()]


def main():
    if not ENRICH_PATH.exists():
        print(f"ERROR: {ENRICH_PATH} not found")
        sys.exit(1)

    with open(ENRICH_PATH, encoding="utf-8") as f:
        enrich = json.load(f)

    csv_lookup = {}
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = (row.get("google_maps_cid") or "").strip()
                if cid:
                    csv_lookup[cid] = row

    total_records = len(enrich)
    records_with_amenities = 0
    all_raw = []
    all_clean = []
    detail_rows = []

    for rec in enrich:
        cid = rec.get("cid", "")
        fields = rec.get("fields") or {}
        amenity_field = fields.get("amenities") or {}
        raw_value = ""
        if isinstance(amenity_field, dict):
            raw_value = amenity_field.get("value", "")
        elif isinstance(amenity_field, str):
            raw_value = amenity_field

        raw_list = parse_amenities(raw_value)
        if not raw_list:
            continue

        records_with_amenities += 1
        business_name = rec.get("business_name") or csv_lookup.get(cid, {}).get("business_name", "") if cid else ""
        area = csv_lookup.get(cid, {}).get("area", "") if cid else ""
        category = csv_lookup.get(cid, {}).get("category", "") if cid else ""

        valid = [a for a in raw_list if is_valid_amenity(a)]
        invalid = [a for a in raw_list if not is_valid_amenity(a)]

        all_raw.extend(raw_list)
        all_clean.extend(valid)

        if invalid:
            detail_rows.append({
                "cid": cid,
                "business": business_name,
                "area": area,
                "category": category,
                "raw_amenities": "; ".join(raw_list),
                "kept": "; ".join(valid) if valid else "",
                "removed": "; ".join(invalid),
                "removed_count": len(invalid),
                "kept_count": len(valid),
            })

    raw_counts = Counter(all_raw)
    clean_counts = Counter(all_clean)
    removed_counts = Counter(all_raw) - Counter(all_clean)

    print("=" * 70)
    print("  AMENITY AUDIT REPORT")
    print("=" * 70)
    print(f"\n  Source: {ENRICH_PATH.name}")
    print(f"  Total records:           {total_records}")
    print(f"  Records with amenities:  {records_with_amenities}")
    print(f"  Total amenity strings:   {len(all_raw)}")
    print(f"  After cleaning:          {len(all_clean)}")
    print(f"  Removed:                 {len(all_raw) - len(all_clean)} "
          f"({(len(all_raw) - len(all_clean)) / len(all_raw) * 100:.0f}%)")
    print(f"  Records with any junk:   {len(detail_rows)}")

    print(f"\n  --- Top 15 raw amenities (BEFORE) ---")
    for name, count in raw_counts.most_common(15):
        print(f"    {name:40s} {count:>4d}")

    if removed_counts:
        print(f"\n  --- Top 15 removed (junk filtered out) ---")
        for name, count in removed_counts.most_common(15):
            print(f"    {name:40s} {count:>4d}")

    print(f"\n  --- Top 15 clean amenities (AFTER) ---")
    for name, count in clean_counts.most_common(15):
        print(f"    {name:40s} {count:>4d}")

    if detail_rows:
        print(f"\n  --- Sample records with removals (first 10) ---")
        for row in detail_rows[:10]:
            print(f"    {row['business'] or '(no name)'} [{row['category']}]")
            print(f"      KEPT:   {row['kept']}")
            print(f"      REMOVED: {row['removed']}")
            print()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "cid", "business", "area", "category",
            "raw_amenities", "kept", "removed",
            "kept_count", "removed_count"
        ])
        writer.writeheader()
        writer.writerows(detail_rows)

    print(f"  --- Summary ---")
    print(f"  Full detail report: {REPORT_PATH}")
    print(f"  Businesses affected:   {len(detail_rows)}")

    unchanged = records_with_amenities - len(detail_rows)
    print(f"  Businesses unchanged:  {unchanged}")
    print(f"  Businesses with amenities: {records_with_amenities}")

    enrich_cids = {r.get("cid") for r in enrich if r.get("cid")}

    lodging_fallback = 0
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat = (row.get("category") or "").strip().lower()
                cid = (row.get("google_maps_cid") or "").strip()
                if cat in ("hotel", "hostel", "vacation_rental") and (not cid or cid not in enrich_cids):
                    lodging_fallback += 1

    if lodging_fallback:
        print(f"\n  --- LODGING FALLBACK ---")
        print(f"  Note: {lodging_fallback} lodging businesses have no CID or no enrich data.")
        print(f"  They'd get guessed amenities from LODGING_AMENITIES:")
        print(f"    hotel:           Free Wi-Fi, Gym, Air conditioning, Free parking, Pet friendly, Pool")
        print(f"    hostel:          Free Wi-Fi, Gym, Pool, Pet friendly, Free parking, Air conditioning")
        print(f"    vacation_rental: Free Wi-Fi, Air conditioning, Pet friendly, Free parking")

    if not detail_rows and not lodging_fallback:
        print(f"\n  [OK] No issues found - amenity data is clean!")
    else:
        print(f"\n  [!]  {len(detail_rows)} records have junk amenities that would be filtered.")
        if lodging_fallback:
            print(f"  [!]  {lodging_fallback} lodging businesses rely on guessed amenities (no enrich data).")

    print("=" * 70)


if __name__ == "__main__":
    main()
