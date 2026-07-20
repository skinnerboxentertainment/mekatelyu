"""Validate launch-critical invariants without changing canonical business records."""

from __future__ import annotations

import csv
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paradisio_app import build


def main() -> int:
    with build.CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    businesses = [build.build_business(row) for row in rows]
    businesses.sort(key=lambda business: business["name"].lower())
    build.dedup_slugs(businesses)
    errors: list[str] = []

    if len(rows) != 738:
        errors.append(f"expected entity-resolved launch baseline of 738 businesses, found {len(rows)}")
    if any(not business["name"].strip() for business in businesses):
        errors.append("blank business name found")
    slugs = [business["slug"] for business in businesses]
    if len(slugs) != len(set(slugs)):
        errors.append("generated slugs are not unique")
    ids = [business["id"] for business in businesses]
    if len(ids) != len(set(ids)):
        errors.append("generated business IDs are not unique")
    cids = [row.get("google_maps_cid", "").strip() for row in rows if row.get("google_maps_cid", "").strip()]
    duplicate_cids = [cid for cid, count in Counter(cids).items() if count > 1]
    if duplicate_cids:
        errors.append(f"duplicate Google Maps CIDs remain: {duplicate_cids}")

    for row, business in zip(rows, [build.build_business(row) for row in rows]):
        if business["category"] != row.get("category", "").strip():
            errors.append(f"semantic enrichment rewrote primary category: {business['name']}")
        if not business["discovery_groups"]:
            errors.append(f"business has no discovery group: {business['name']}")
        if row.get("category", "").strip() in {"hotel", "hostel", "vacation_rental"}:
            if "stay" not in business["discovery_groups"]:
                errors.append(f"lodging omitted from Places to Stay: {business['name']}")
        whatsapp = business["channels"]["whatsapp"]
        if whatsapp and not row.get("whatsapp", "").strip():
            errors.append(f"inferred WhatsApp route: {business['name']}")
        if whatsapp and not whatsapp.startswith("+"):
            errors.append(f"non-international WhatsApp route: {business['name']}")
        phone = business["channels"]["phone_normalized"]
        if phone and not phone.startswith("+"):
            errors.append(f"non-international phone route: {business['name']}")
        if business["status"] in {"closed", "permanently_closed"}:
            if business["primary_contact"]["type"] != "None" or business["secondary_links"]:
                errors.append(f"closed business exposes contact action: {business['name']}")
        for key in ("website", "facebook_url", "booking_url", "tripadvisor_url"):
            value = business["channels"][key]
            if value and not value.startswith("https://"):
                errors.append(f"unsafe external URL for {business['name']}: {key}")
        if business["lat"] or business["lng"]:
            try:
                lat = float(business["lat"])
                lng = float(business["lng"])
                if not (math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180):
                    raise ValueError
            except ValueError:
                errors.append(f"invalid coordinate pair: {business['name']}")

    status_counts = Counter(business["status"] for business in businesses)
    primary_counts = Counter(business["primary_contact"]["type"] for business in businesses)
    print(f"Businesses: {len(businesses)}")
    print(f"Statuses: {dict(status_counts)}")
    print(f"Primary actions: {dict(primary_counts)}")
    print(f"Explicit WhatsApp routes: {sum(bool(b['channels']['whatsapp']) for b in businesses)}")
    print(f"Valid call routes: {sum(bool(b['channels']['phone_normalized']) for b in businesses)}")
    print(f"Semantic records: {len(businesses)}")
    print(f"Semantic review queue: {sum(b['semantic_review_state'] == 'review' for b in businesses)}")

    if errors:
        print(f"FAIL: {len(errors)} source-data invariant error(s)")
        for error in errors[:50]:
            print(f"- {error}")
        return 1
    print("PASS: launch-critical source-data invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
