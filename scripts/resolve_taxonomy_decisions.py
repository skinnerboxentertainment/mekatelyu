"""Apply the owner-authorized resolution of the 23 semantic taxonomy decisions."""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from pathlib import Path

from autovisual_whatsapp_checkifier import record_id

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "pv_master_unified.csv"
REVIEW = ROOT / "audit" / "semantic-taxonomy" / "review-queue.json"
MANIFEST = ROOT / "audit" / "semantic-taxonomy" / "resolved-primary-categories.csv"

# business, area, expected current, resolved primary, disposition, evidence rationale
DECISIONS = (
    ("Adobe EasyCar Rent a Car", "Puerto Viejo", "tour_company", "transport", "corrected", "Canonical description explicitly identifies car rental."),
    ("Alamo Enterprise Car Rental", "Puerto Viejo", "tour_company", "transport", "corrected", "Canonical description explicitly identifies car rental."),
    ("ALMA Masajes", "Playa Negra", "restaurant", "wellness", "corrected", "Business identity and captured amenities identify massage/spa services."),
    ("Alojamiento kon-tiky", "Playa Negra", "restaurant", "vacation_rental", "corrected", "CID focus identifies private lodging and vacation apartment rental."),
    ("Ariel Apartment's", "Playa Negra", "restaurant", "vacation_rental", "corrected", "CID focus explicitly identifies a tourist apartment."),
    ("Arrecife Hotel y Restaurante - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica", "Punta Uva", "restaurant", "restaurant", "retained_mixed_use", "Description leads with restaurant/bar and separately confirms cabina rentals."),
    ("Beauty Ritual Spa", "Cocles", "restaurant", "wellness", "corrected", "CID focus explicitly identifies a health and wellness center/spa."),
    ("Blessed Hands Massage Therapy", "Playa Negra", "restaurant", "wellness", "corrected", "Business identity and captured amenity identify massage therapy."),
    ("Blue Dreams Hotel", "Playa Negra", "restaurant", "hotel", "corrected", "Business identity and canonical description explicitly identify a hotel."),
    ("Cabina trepazul", "Playa Negra", "restaurant", "vacation_rental", "corrected", "CID focus explicitly identifies lodging."),
    ("Caribbean Blue Morpho Casitas", "Playa Negra", "restaurant", "vacation_rental", "corrected", "CID focus identifies hotel/vacation accommodation and rooms."),
    ("Caribe Shuttle", "Puerto Viejo", "tour_company", "transport", "corrected", "CID and description explicitly identify shuttle transportation."),
    ("Casa del Caribe B&B", "Playa Negra", "restaurant", "hotel", "corrected", "Business identity and CID focus identify B&B/homestay lodging."),
    ("Casita Tucan", "Cocles", "restaurant", "hotel", "corrected", "CID focus explicitly identifies a three-star hotel."),
    ("Casitas Batsú", "Cocles", "restaurant", "vacation_rental", "corrected", "CID focus explicitly identifies holiday apartment rental."),
    ("Douglas Ville guest house", "Playa Negra", "restaurant", "vacation_rental", "corrected", "Business identity explicitly identifies a guest house."),
    ("Hawaiian Massage", "Playa Negra", "restaurant", "wellness", "corrected", "CID focus explicitly identifies a massage center."),
    ("La Casita de Monli", "Puerto Viejo", "restaurant", "restaurant", "retained_false_positive", "CID and description explicitly identify a seafood restaurant; 'Casita' is its name."),
    ("Le Caméléon - Playa Cocles, Puerto Viejo, Limón, Costa Rica", "Cocles", "hotel", "hotel", "retained_mixed_use", "Description clearly identifies a hotel; bar remains a secondary quality."),
    ("Morpho Casitas", "Playa Negra", "restaurant", "vacation_rental", "corrected", "Alias/business identity identifies casita accommodation; corroborated by linked Morpho property evidence."),
    ("Namu Garden Hotel & Spa", "Playa Negra", "restaurant", "hotel", "corrected", "Business identity explicitly identifies a hotel with spa as a secondary quality."),
    ("Selvin's Restaurant and Cabinas - Playa Punta Uva, Puerto Viejo, Limón, Costa Rica", "Punta Uva", "restaurant", "restaurant", "retained_mixed_use", "Description leads with restaurant and separately confirms rooms/house for rent."),
    ("Sloth Massage", "Puerto Viejo", "restaurant", "wellness", "corrected", "CID reviews and business identity explicitly describe massage services."),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    review_ids = {item["key"] for item in review}
    if len(review_ids) != 23 or len(DECISIONS) != 23:
        raise SystemExit(f"refusing resolution: expected 23 review records and decisions, found {len(review_ids)} and {len(DECISIONS)}")

    by_record = {record_id(row["business_name"], row.get("area", "")): row for row in rows}
    manifest = []
    changed = 0
    for name, area, expected, resolved, disposition, rationale in DECISIONS:
        identifier = record_id(name, area)
        row = by_record.get(identifier)
        if not row:
            raise SystemExit(f"refusing resolution: missing master record {name} / {area}")
        semantic_key = f"cid:{row['google_maps_cid'].strip()}" if row.get("google_maps_cid", "").strip() else f"record:{identifier}"
        if semantic_key not in review_ids:
            raise SystemExit(f"refusing resolution: record is not in current semantic review queue: {name}")
        if row.get("category", "") != expected:
            raise SystemExit(f"refusing resolution: stale category for {name}: expected {expected}, found {row.get('category', '')}")
        if expected != resolved:
            changed += 1
        manifest.append({
            "record_id": identifier, "business_name": name, "area": area,
            "old_category": expected, "resolved_category": resolved,
            "disposition": disposition, "rationale": rationale,
        })

    if changed != 19:
        raise SystemExit(f"refusing resolution: expected 19 category corrections, found {changed}")
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=manifest[0].keys(), lineterminator="\n")
        writer.writeheader(); writer.writerows(manifest)
    if not args.apply:
        print(f"DRY RUN: 23 decisions resolved; {changed} category corrections and {23-changed} retentions")
        return 0

    resolved_by_id = {row["record_id"]: row["resolved_category"] for row in manifest}
    for row in rows:
        identifier = record_id(row["business_name"], row.get("area", ""))
        if identifier in resolved_by_id:
            row["category"] = resolved_by_id[identifier]
    descriptor, temporary_name = tempfile.mkstemp(prefix=".pv_master_unified.", suffix=".csv", dir=MASTER.parent)
    os.close(descriptor); temporary = Path(temporary_name)
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
            writer.writeheader(); writer.writerows(rows)
        os.replace(temporary, MASTER)
    finally:
        if temporary.exists(): temporary.unlink()
    print(f"APPLIED: {changed} category corrections; {23-changed} reviewed retentions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
