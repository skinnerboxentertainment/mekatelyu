"""Deterministic, provenance-backed discovery taxonomy for Paradisio."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

TAXONOMY_VERSION = "2026-07-21.1"

GROUP_LABELS = {
    "stay": "Places to Stay",
    "eat": "Eat & Drink",
    "things-to-do": "Things to Do",
    "shopping": "Shopping",
    "wellness": "Wellness",
    "services": "Services",
    "nightlife": "Nightlife",
    "transport": "Transport",
}

PRIMARY_CATEGORY_GROUPS = {
    "hotel": ("stay",),
    "hostel": ("stay",),
    "vacation_rental": ("stay",),
    "restaurant": ("eat",),
    "tour_company": ("things-to-do",),
    "shopping": ("shopping",),
    "wellness": ("wellness",),
    "nightlife": ("nightlife", "eat"),
    "transport": ("transport",),
    "services": ("services",),
    "real_estate": ("services",),
}

PRIMARY_CATEGORY_TAGS = {
    "hotel": "hotel",
    "hostel": "hostel",
    "vacation_rental": "vacation-rental",
    "restaurant": "restaurant",
    "tour_company": "tour-operator",
    "shopping": "shop",
    "wellness": "wellness",
    "nightlife": "nightlife",
    "transport": "transport",
    "services": "local-service",
    "real_estate": "real-estate",
}

TAG_LABELS = {
    "hotel": "Hotel", "hostel": "Hostel", "vacation-rental": "Vacation Rental",
    "bed-and-breakfast": "Bed & Breakfast", "ecolodge": "Ecolodge", "cabins": "Cabins",
    "restaurant": "Restaurant", "cafe": "Café", "bakery": "Bakery",
    "ice-cream": "Ice Cream", "bar": "Bar", "grocery": "Grocery",
    "tour-operator": "Tours", "surf": "Surf", "diving": "Diving",
    "snorkeling": "Snorkeling", "kayaking": "Kayaking", "fishing": "Fishing",
    "wildlife": "Wildlife", "yoga": "Yoga", "massage": "Massage", "spa": "Spa",
    "gym": "Gym", "shop": "Shop", "clothing": "Clothing", "pharmacy": "Pharmacy",
    "supermarket": "Supermarket", "local-service": "Local Service", "real-estate": "Real Estate",
    "laundry": "Laundry", "medical": "Medical", "dental": "Dental", "beauty": "Beauty",
    "banking": "Banking", "nightlife": "Nightlife", "live-music": "Live Music",
    "transport": "Transport", "shuttle": "Shuttle", "taxi": "Taxi", "car-rental": "Car Rental",
}

TAG_GROUPS = {
    "hotel": ("stay",), "hostel": ("stay",), "vacation-rental": ("stay",),
    "bed-and-breakfast": ("stay",), "ecolodge": ("stay",), "cabins": ("stay",),
    "restaurant": ("eat",), "cafe": ("eat",), "bakery": ("eat",),
    "ice-cream": ("eat",), "bar": ("eat", "nightlife"), "grocery": ("shopping",),
    "tour-operator": ("things-to-do",), "surf": ("things-to-do",),
    "diving": ("things-to-do",), "snorkeling": ("things-to-do",),
    "kayaking": ("things-to-do",), "fishing": ("things-to-do",),
    "wildlife": ("things-to-do",), "yoga": ("wellness", "things-to-do"),
    "massage": ("wellness",), "spa": ("wellness",), "gym": ("wellness",),
    "shop": ("shopping",), "clothing": ("shopping",), "pharmacy": ("shopping", "services"),
    "supermarket": ("shopping",), "local-service": ("services",), "real-estate": ("services",),
    "laundry": ("services",), "medical": ("services", "wellness"),
    "dental": ("services", "wellness"), "beauty": ("services", "wellness"),
    "banking": ("services",), "nightlife": ("nightlife",), "live-music": ("nightlife",),
    "transport": ("transport",), "shuttle": ("transport",), "taxi": ("transport",),
    "car-rental": ("transport",),
}

GROUP_SYNONYMS = {
    "stay": ("stay", "stays", "lodging", "accommodation", "places to stay", "hospedaje", "alojamiento"),
    "eat": ("eat", "drink", "food", "dining", "restaurants", "comer", "bebidas"),
    "things-to-do": ("things to do", "activities", "tours", "adventures", "actividades", "paseos"),
    "shopping": ("shopping", "shops", "stores", "tiendas", "compras"),
    "wellness": ("wellness", "health", "bienestar", "salud"),
    "services": ("services", "local services", "servicios"),
    "nightlife": ("nightlife", "evening", "bars", "vida nocturna"),
    "transport": ("transport", "transportation", "getting around", "transporte"),
}


@dataclass(frozen=True)
class TagRule:
    tag: str
    patterns: tuple[str, ...]


TAG_RULES = (
    TagRule("hotel", (r"\bhotel\b", r"\blodge\b", r"\bposada\b")),
    TagRule("hostel", (r"\bhostel\b", r"\balbergue\b")),
    TagRule("vacation-rental", (r"\bvacation rental\b", r"\bholiday home\b", r"\bapartments?\b",
                                r"\bvillas?\b", r"\bguest\s*house\b", r"\bcasitas\b",
                                r"\balojamiento\b", r"\bhospedaje\b")),
    TagRule("bed-and-breakfast", (r"\bbed\s*(?:&|and)\s*breakfast\b", r"\bb\s*&\s*b\b")),
    TagRule("ecolodge", (r"\beco[ -]?lodge\b", r"\becological lodge\b")),
    TagRule("cabins", (r"\bcabinas?\b", r"\bcabins?\b", r"\bcabañas?\b")),
    TagRule("cafe", (r"\bcaf[eé]\b", r"\bcafeter[ií]a\b", r"\bcoffee shop\b")),
    TagRule("bakery", (r"\bbakery\b", r"\bpanader[ií]a\b", r"\bpasteler[ií]a\b")),
    TagRule("ice-cream", (r"\bice cream\b", r"\bhelader[ií]a\b", r"\bgelato\b")),
    TagRule("bar", (r"\bbar\b", r"\bpub\b", r"\bcocktail(?:s)?\b")),
    TagRule("supermarket", (r"\bsupermarket\b", r"\bsupermercado\b")),
    TagRule("grocery", (r"\bgrocery\b", r"\btienda de comestibles\b")),
    TagRule("surf", (r"\bsurf(?:ing)?\b", r"\bsurf school\b", r"\bescuela de surf\b")),
    TagRule("diving", (r"\bscuba\b", r"\bdiv(?:e|ing)\b", r"\bbuceo\b")),
    TagRule("snorkeling", (r"\bsnorkel(?:ing)?\b",)),
    TagRule("kayaking", (r"\bkayak(?:ing)?\b",)),
    TagRule("fishing", (r"\bfishing\b", r"\bpesca\b")),
    TagRule("wildlife", (r"\bwildlife\b", r"\banimal rescue\b", r"\brescate animal\b")),
    TagRule("yoga", (r"\byoga\b", r"\bacroyoga\b")),
    TagRule("massage", (r"\bmassage\b", r"\bmasajes?\b")),
    TagRule("spa", (r"\bspa\b",)),
    TagRule("gym", (r"\bgym\b", r"\bgimnasio\b", r"\bfitness\b")),
    TagRule("clothing", (r"\bclothing\b", r"\btienda de ropa\b", r"\bropa\b")),
    TagRule("pharmacy", (r"\bpharmacy\b", r"\bfarmacia\b")),
    TagRule("real-estate", (r"\breal estate\b", r"\bbienes ra[ií]ces\b", r"\binmobiliaria\b")),
    TagRule("laundry", (r"\blaundry\b", r"\blavander[ií]a\b")),
    TagRule("medical", (r"\bmedical\b", r"\bclinic(?:a)?\b", r"\bcl[ií]nica\b", r"\bdoctor(?:s)?\b")),
    TagRule("dental", (r"\bdent(?:al|ist)\b", r"\bdentista\b", r"\bodontolog")),
    TagRule("beauty", (r"\bbeauty\b", r"\bsalon\b", r"\bsal[oó]n\b", r"\bbarber")),
    TagRule("banking", (r"\bbank\b", r"\bbanco\b", r"\batm\b", r"\bcajero\b")),
    TagRule("live-music", (r"\blive music\b", r"\bm[uú]sica en vivo\b")),
    TagRule("shuttle", (r"\bshuttle\b", r"\btransfer(?:s)?\b")),
    TagRule("taxi", (r"\btaxi\b",)),
    TagRule("car-rental", (r"\bcar rental\b", r"\brent a car\b", r"\balquiler de (?:autos|carros|coches)\b")),
)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"\s+", " ", value).strip()


def semantic_key(row: dict[str, str]) -> str:
    cid = (row.get("google_maps_cid") or "").strip()
    if cid:
        return f"cid:{cid}"
    raw = f"{(row.get('business_name') or '').strip()}|{(row.get('area') or '').strip()}"
    return "record:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def classify_record(row: dict[str, str], parsed: dict | None = None) -> dict:
    parsed = parsed or {}
    primary = normalize_text(row.get("category", "")).replace(" ", "_")
    name = normalize_text(row.get("business_name", ""))
    description = normalize_text(row.get("description_full", ""))
    fields = parsed.get("fields") or {}

    def field_value(field: str) -> str:
        value = fields.get(field, "")
        value = value.get("value", "") if isinstance(value, dict) else value
        if isinstance(value, list):
            value = " ".join(str(item) for item in value)
        return normalize_text(str(value or ""))

    evidence_sources = {
        "master_name": name,
        "master_description": description,
        "maps_subcategory": field_value("subcategory"),
        "maps_cuisine": field_value("cuisine"),
        "maps_amenities": normalize_text(" ".join(field_value("amenities").splitlines())),
    }
    assertions: dict[str, dict] = {}

    primary_tag = PRIMARY_CATEGORY_TAGS.get(primary)
    if primary_tag:
        assertions[primary_tag] = {
            "confidence": 1.0,
            "source": "master.category",
            "rule": f"primary:{primary}",
            "evidence": row.get("category", ""),
        }

    # Only focused identity/description and parsed fields are eligible. Raw Maps page text is
    # intentionally retained in evidence packets but excluded here because navigation labels can
    # create false semantic matches (for example every Maps page mentioning nearby hotels).
    eligible = ("master_name", "master_description", "maps_subcategory", "maps_cuisine", "maps_amenities")
    for rule in TAG_RULES:
        if rule.tag in assertions:
            continue
        for source in eligible:
            text = evidence_sources[source]
            match = next((re.search(pattern, text, flags=re.IGNORECASE) for pattern in rule.patterns if re.search(pattern, text, flags=re.IGNORECASE)), None)
            if match:
                confidence = 0.96 if source == "master_name" else 0.92 if source == "master_description" else 0.90
                assertions[rule.tag] = {
                    "confidence": confidence,
                    "source": source.replace("_", ".", 1),
                    "rule": f"explicit:{rule.tag}",
                    "evidence": match.group(0),
                }
                break

    identity_sources = {"master.category", "master.name", "maps.subcategory", "maps.cuisine"}
    tags = sorted(tag for tag, assertion in assertions.items() if assertion["source"] in identity_sources)
    attributes = sorted(tag for tag, assertion in assertions.items() if assertion["source"] not in identity_sources)
    groups = set(PRIMARY_CATEGORY_GROUPS.get(primary, ()))
    for tag in tags:
        groups.update(TAG_GROUPS.get(tag, ()))
    groups = sorted(groups)
    synonyms = sorted({term for group in groups for term in GROUP_SYNONYMS.get(group, ())} | {
        TAG_LABELS.get(tag, tag).lower() for tag in tags + attributes
    })
    conflicts = []
    if not primary:
        conflicts.append("missing_primary_category")
    if not groups:
        conflicts.append("no_discovery_group")
    if primary == "restaurant" and "stay" in groups:
        conflicts.append("restaurant_with_lodging_evidence")
    if primary == "restaurant" and any(group in groups for group in ("wellness", "services", "transport")):
        conflicts.append("restaurant_with_non_food_identity")
    if primary in {"hotel", "hostel", "vacation_rental"} and "eat" in groups:
        conflicts.append("lodging_with_food_evidence")
    if primary == "tour_company" and "transport" in groups:
        conflicts.append("tour_company_with_transport_identity")

    return {
        "key": semantic_key(row),
        "business_name": row.get("business_name", ""),
        "area": row.get("area", ""),
        "google_maps_cid": row.get("google_maps_cid", ""),
        "primary_category": primary,
        "groups": groups,
        "tags": tags,
        "attributes": attributes,
        "search_synonyms": synonyms,
        "assertions": assertions,
        "evidence_coverage": {
            "master_description": bool(description),
            "maps_parsed": bool(parsed),
            "maps_subcategory": bool(evidence_sources["maps_subcategory"]),
        },
        "conflicts": conflicts,
        "review_state": "review" if conflicts else "accepted_deterministic",
        "taxonomy_version": TAXONOMY_VERSION,
    }
