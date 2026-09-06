import csv
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import qrcode
from PIL import Image

try:
    from . import domain, freshness, i18n, provenance, viewmodels
    from .semantic_taxonomy import TAG_LABELS, TAXONOMY_VERSION, classify_record, semantic_key
except ImportError:  # Direct execution: python paradisio_app/build.py
    import domain
    import freshness
    import i18n
    import provenance
    import viewmodels
    from semantic_taxonomy import TAG_LABELS, TAXONOMY_VERSION, classify_record, semantic_key
try:
    from .community_partner import load_organizations, public_org_summary, render_organization_html
except ImportError:
    from community_partner import load_organizations, public_org_summary, render_organization_html

ICONS = {
    "Instagram": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><circle cx="12" cy="12" r="5"/><circle cx="17.5" cy="6.5" r="1.5" fill="currentColor" stroke="none"/></svg>',
    "WhatsApp": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>',
    "Facebook": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>',
    "Website": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    "Google Maps": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    "Call": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    "Directions": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "Share": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
    "Booking.com": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7"/><rect x="3" y="3" width="18" height="4" rx="1"/></svg>',
    "TripAdvisor": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="12" r="4"/><circle cx="18" cy="12" r="4"/><path d="M12 16c-1.5 1-4 1-4 0s2.5-4 4-4 4 3 4 4-2.5-1-4 0z"/></svg>',
    "Email": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
}

PLACEHOLDER_PATTERNS = [
    r'^[A-Z][a-zA-Z0-9\s\-\'\u00c0-\u024f]+ is (a|an) ',
    r' provides?\s+(hotel|accommodation|service)',
    r' offers?\s+(service)',
    r'^[A-Z].+? (provides|offers) .+ in (Puerto Viejo|Cocles|Cahuita|Manzanillo)',
]

def is_auto_description(text):
    if not text:
        return True
    text = text.strip()
    if len(text) < 100:
        return True
    return any(re.search(pat, text, re.I) for pat in PLACEHOLDER_PATTERNS)


def description_facts(row, enrich):
    """The ingredients of an auto-written description, as data.

    Returned as (key, params) pairs rather than a finished sentence so the
    description can be rendered in whichever language the page is being built
    for. Descriptions written by a business are never touched — only the ones
    this generator composes itself.
    """
    # The category is carried as its key, not as an English label, so the
    # sentence can be composed in the language of the page being built.
    facts = [("desc.category_in_area", {
        "category_key": row.get("category", "").strip(),
        "area": row.get("area", "").strip() or "Puerto Viejo",
    })]
    rating = enrich.get("rating") if enrich else None
    if rating:
        facts.append(("desc.rated", {"rating": rating}))
    else:
        verified = row.get("verified_date", "").strip()[:7] if row.get("verified_date") else ""
        if verified:
            facts.append(("desc.listed_since", {"month": verified}))
    if row.get("phone") or row.get("normalized_phone"):
        facts.append(("desc.phone", {}))
    if row.get("instagram_handle", "").strip():
        facts.append(("desc.instagram", {}))
    if row.get("whatsapp", "").strip():
        facts.append(("desc.whatsapp", {}))
    if row.get("email", "").strip():
        facts.append(("desc.email", {}))
    return facts


def infer_amenities(row, enrich_amenities, verified_amenities):
    """Resolve the amenity list for a business.

    Priority:
      1. Verified amenity data from the amenity pipeline (evidence-backed).
         These names are already normalized and validated upstream, so they
         bypass the legacy OCR filter entirely.
      2. Legacy OCR enrichment (maps_parsed_v3) — coarser, unverified.
      3. Nothing. We do NOT inject statistical defaults, because doing so
         fabricates amenities businesses may not actually offer.
    """
    if verified_amenities:
        available = verified_amenities.get("availableNames", [])
        if available:
            return [a for a in available if a and a.strip()]
    # Legacy OCR enrichment (maps_parsed_v3) is intentionally NOT used for
    # amenities: it is coarse, Spanish, and unverified, and has been shown to
    # attribute amenities to the wrong businesses. Amenities come only from
    # evidence-backed verified data. No statistical defaults are injected.
    return []

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
REPO_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.environ.get("PARADISIO_OUTPUT_DIR", REPO_DIR / "release")).resolve()
CSV_PATH = BASE_DIR.parent / "pv_master_unified.csv"
MAPS_ENRICH_PATH = BASE_DIR / "data" / "maps_parsed_v3.json"
VERIFIED_AMENITIES_PATH = BASE_DIR / "data" / "verified_amenities.json"
VERIFIED_ATTRIBUTES_PATH = BASE_DIR / "data" / "verified_attributes.json"
VERIFIED_HOURS_PATH = BASE_DIR / "data" / "verified_hours.json"
SEMANTIC_TAXONOMY_PATH = BASE_DIR / "data" / "semantic_taxonomy.json"
def build_date():
    """Return the build date stamped into the output.

    Reads PARADISIO_BUILD_DATE so a rebuild of unchanged inputs is byte-identical
    across days, which is what makes golden-output comparison possible. Falls back
    to today when unset. An unparseable value fails closed rather than silently
    reintroducing a nondeterministic stamp.
    """
    raw = os.environ.get("PARADISIO_BUILD_DATE", "").strip()
    if not raw:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise SystemExit(f"PARADISIO_BUILD_DATE must be YYYY-MM-DD, got: {raw!r}") from None


def build_today():
    """The build date as a `date`, for anything that ages a record.

    Freshness must be judged against the *injected* build date, never the wall
    clock. Assessing against `date.today()` puts the wall clock back into the
    emitted HTML: as records cross their staleness thresholds the rendered
    provenance text changes, and the golden manifest breaks on a day nobody
    touched the code. This is the same guarantee `build_date()` gives the footer.
    """
    return datetime.strptime(build_date(), "%Y-%m-%d").date()


def load_verified_hours():
    """Load the verified operating-hours lookup (CID-keyed) from the pipeline."""
    path = VERIFIED_HOURS_PATH
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_verified_attributes():
    """Load the verified About-attributes lookup (CID-keyed) from the pipeline.

    Returns a dict of {cid: {"attributes": [{"group": ..., "items": [...]}]}}.
    """
    path = VERIFIED_ATTRIBUTES_PATH
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_verified_amenities():
    """Load the verified amenity lookup (CID-keyed) from the amenity pipeline.

    Returns a dict of {cid: {"availableNames": [...], "unavailableNames": [...]}}.
    """
    path = VERIFIED_AMENITIES_PATH
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for cid, rec in data.items():
        if not cid:
            continue
        result[cid] = {
            "availableNames": rec.get("availableNames", []),
            "unavailableNames": rec.get("unavailableNames", []),
            "sourceName": rec.get("sourceName", ""),
        }
    return result


def load_maps_enrich():
    path = MAPS_ENRICH_PATH
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    lookup = {}
    for r in records:
        cid = r.get("cid", "")
        if not cid:
            continue
        # v3 format: fields keyed with value/confidence wrappers
        if r.get("fields"):
            flat = {}
            for field, data in r["fields"].items():
                if isinstance(data, dict) and "value" in data:
                    flat[field] = data["value"]
                elif not isinstance(data, dict):
                    flat[field] = data
                else:
                    flat[field] = data.get("value", "")
            # Extract plus_code from address if present
            if "address" in flat and isinstance(r["fields"].get("address"), dict):
                flat["plus_code"] = r["fields"]["address"].get("plus_code", "")
            lookup[cid] = flat
        # v2 format: direct data object
        elif r.get("success") and r.get("data"):
            lookup[cid] = r["data"]
    return lookup

WHATSAPP_TEMPLATE = "Hi {name}, I found you on Whappin Puerto Viejo. Are you open? I'd like to know more about your services. Thanks."

# The contact-safety and naming rules now live in domain.py, so every surface
# that publishes a route goes through the same validation. These names are kept
# as the module's public API: existing tests and scripts bind to build.* and the
# behaviour is identical.
LOCATION_TOKENS = domain.LOCATION_TOKENS
clean_display_name = domain.clean_display_name
slugify = domain.slugify
normalize_phone = domain.normalize_phone
safe_external_url = domain.safe_external_url
safe_instagram_handle = domain.safe_instagram_handle


def dedup_slugs(businesses):
    seen = {}
    for biz in businesses:
        slug = biz["slug"]
        if slug in seen:
            n = seen[slug] + 1
            seen[slug] = n
            biz["slug"] = f"{slug}-{n}"
        else:
            seen[slug] = 0
    return businesses


def compute_id(row):
    return domain.record_id(
        row.get("business_name", ""), row.get("google_maps_cid", ""), row.get("phone", "")
    )


def has_whatsapp(row):
    """Return an explicit WhatsApp destination in international digits.

    Ordinary phone numbers are deliberately not inferred as WhatsApp-capable.
    """
    return domain.explicit_whatsapp(row.get("whatsapp", ""))


def contactability_score(row):
    score = 0
    if has_whatsapp(row): score += 40
    if row.get("phone", "").strip(): score += 30
    if safe_instagram_handle(row.get("instagram_handle", "")): score += 15
    if row.get("website", "").strip(): score += 10
    if row.get("facebook_url", "").strip(): score += 5
    return min(score, 100)


def visibility_score(row):
    score = 0
    if row.get("google_maps_cid", "").strip(): score += 35
    if row.get("latitude", "").strip(): score += 25
    if row.get("booking_url", "").strip(): score += 15
    if row.get("tripadvisor_url", "").strip(): score += 10
    if row.get("email", "").strip(): score += 5
    ig_conf = row.get("instagram_confidence", "").strip()
    if ig_conf == "verified": score += 10
    return min(score, 100)


def completeness_score(row):
    score = 0
    if row.get("business_name", "").strip(): score += 10
    if row.get("category", "").strip(): score += 10
    if row.get("area", "").strip(): score += 10
    if row.get("latitude", "").strip(): score += 15
    if row.get("phone", "").strip() or row.get("normalized_phone", "").strip(): score += 10
    if row.get("website", "").strip(): score += 10
    if row.get("instagram_handle", "").strip() or row.get("facebook_url", "").strip(): score += 10
    if row.get("description_full", "").strip(): score += 10
    if row.get("operating_status", "").strip(): score += 5
    if row.get("verified_date", "").strip(): score += 10
    return min(score, 100)


def get_badges(row):
    if row.get("operating_status", "").strip().lower() in {"closed", "permanently_closed"}:
        return []
    badges = []
    if has_whatsapp(row): badges.append("WhatsApp")
    ig = safe_instagram_handle(row.get("instagram_handle", ""))
    ig_conf = row.get("instagram_confidence", "").strip()
    if ig and ig_conf == "verified": badges.append("Instagram")
    if row.get("booking_url", "").strip(): badges.append("Booking")
    if safe_external_url(row.get("website", "")): badges.append("Website")
    return badges


def get_primary_contact(row):
    if row.get("operating_status", "").strip().lower() in {"closed", "permanently_closed"}:
        return {"type": "None", "label": "Closed", "url": ""}
    wp = has_whatsapp(row)
    if wp:
        message = WHATSAPP_TEMPLATE.format(name=row.get("business_name", ""))
        return {
            "type": "WhatsApp",
            "label": "Message on WhatsApp",
            "url": f"https://wa.me/{wp.lstrip('+')}?text={quote(message)}",
        }
    phone = normalize_phone(row.get("normalized_phone", "") or row.get("phone", ""))
    if phone:
        return {"type": "Call", "label": "Call", "url": f"tel:{phone}"}
    ig = safe_instagram_handle(row.get("instagram_handle", ""))
    if ig:
        return {"type": "Instagram", "label": "Instagram DM", "url": f"https://instagram.com/{ig}"}
    website = safe_external_url(row.get("website", ""))
    if website:
        return {"type": "Website", "label": "Visit Website", "url": website}
    cid = row.get("google_maps_cid", "").strip()
    if cid:
        return {"type": "Map", "label": "Open in Maps", "url": f"https://www.google.com/maps?cid={cid}"}
    lat = row.get("latitude", "").strip()
    lng = row.get("longitude", "").strip()
    if lat and lng:
        return {"type": "Map", "label": "View Location", "url": f"https://www.google.com/maps/search/{lat},{lng}"}
    return {"type": "None", "label": "No contact available", "url": "#"}


def get_secondary_links(row):
    if row.get("operating_status", "").strip().lower() in {"closed", "permanently_closed"}:
        return []
    links = []
    phone = normalize_phone(row.get("normalized_phone", "") or row.get("phone", ""))
    if phone:
        links.append({"label": "Call", "url": f"tel:{phone}"})
    ig = safe_instagram_handle(row.get("instagram_handle", ""))
    if ig:
        links.append({"label": "Instagram", "url": f"https://instagram.com/{ig}"})
    fb = safe_external_url(row.get("facebook_url", ""))
    if fb:
        links.append({"label": "Facebook", "url": fb})
    website = safe_external_url(row.get("website", ""))
    if website:
        links.append({"label": "Website", "url": website})
    booking = safe_external_url(row.get("booking_url", ""))
    if booking:
        links.append({"label": "Booking.com", "url": booking})
    ta = safe_external_url(row.get("tripadvisor_url", ""))
    if ta:
        links.append({"label": "TripAdvisor", "url": ta})
    cid = row.get("google_maps_cid", "").strip()
    if cid:
        links.append({"label": "Google Maps", "url": f"https://www.google.com/maps?cid={cid}"})
    elif row.get("latitude", "").strip() and row.get("longitude", "").strip():
        lat = row["latitude"].strip()
        lng = row["longitude"].strip()
        links.append({"label": "Google Maps", "url": f"https://www.google.com/maps/search/{lat},{lng}"})
    return links


PROVENANCE_INDEX = None


def provenance_index():
    global PROVENANCE_INDEX
    if PROVENANCE_INDEX is None:
        PROVENANCE_INDEX = provenance.ProvenanceIndex()
    return PROVENANCE_INDEX


MAPS_CACHE = None
SEMANTIC_CACHE = None
VERIFIED_AMENITIES_CACHE = None
VERIFIED_ATTRIBUTES_CACHE = None
VERIFIED_HOURS_CACHE = None


def maps_data(cid):
    global MAPS_CACHE
    if MAPS_CACHE is None:
        MAPS_CACHE = load_maps_enrich()
    return MAPS_CACHE.get(cid, {})


def verified_amenity_data(cid):
    global VERIFIED_AMENITIES_CACHE
    if VERIFIED_AMENITIES_CACHE is None:
        VERIFIED_AMENITIES_CACHE = load_verified_amenities()
    return VERIFIED_AMENITIES_CACHE.get(cid, {})


def verified_attribute_data(cid):
    global VERIFIED_ATTRIBUTES_CACHE
    if VERIFIED_ATTRIBUTES_CACHE is None:
        VERIFIED_ATTRIBUTES_CACHE = load_verified_attributes()
    return VERIFIED_ATTRIBUTES_CACHE.get(cid, {})


def verified_hour_data(cid):
    global VERIFIED_HOURS_CACHE
    if VERIFIED_HOURS_CACHE is None:
        VERIFIED_HOURS_CACHE = load_verified_hours()
    return VERIFIED_HOURS_CACHE.get(cid, {})


def semantic_data(row):
    global SEMANTIC_CACHE
    if SEMANTIC_CACHE is None:
        if SEMANTIC_TAXONOMY_PATH.exists():
            with open(SEMANTIC_TAXONOMY_PATH, encoding="utf-8") as handle:
                SEMANTIC_CACHE = json.load(handle).get("records", {})
        else:
            SEMANTIC_CACHE = {}
    return SEMANTIC_CACHE.get(semantic_key(row)) or classify_record(row)


def build_business(row):
    name = clean_display_name(row.get("business_name", "").strip(), row.get("area", "").strip())
    area = row.get("area", "").strip()
    slug = slugify(row.get("business_name", "").strip(), area)
    cid = row.get("google_maps_cid", "").strip()
    enrich = maps_data(cid)
    verified_amenities = verified_amenity_data(cid)
    verified_attributes = verified_attribute_data(cid)
    verified_hours = verified_hour_data(cid)
    semantic = semantic_data(row)
    business = {
        "id": compute_id(row),
        "slug": slug,
        "name": name,
        "category": row.get("category", "").strip(),
        "area": area or "Unknown",
        "lat": row.get("latitude", "").strip(),
        "lng": row.get("longitude", "").strip(),
        "distance_km": row.get("distance_km", "").strip(),
        "status": row.get("operating_status", "").strip() or "unknown",
        "channels": {
            "phone": row.get("phone", "").strip() if normalize_phone(row.get("normalized_phone", "") or row.get("phone", "")) else "",
            "phone_normalized": normalize_phone(row.get("normalized_phone", "") or row.get("phone", "")),
            "whatsapp": has_whatsapp(row),
            "instagram": safe_instagram_handle(row.get("instagram_handle", "")),
            "instagram_verified": row.get("instagram_confidence", "").strip() == "verified",
            "facebook_url": safe_external_url(row.get("facebook_url", "")),
            "website": safe_external_url(row.get("website", "")),
            "booking_url": safe_external_url(row.get("booking_url", "")),
            "tripadvisor_url": safe_external_url(row.get("tripadvisor_url", "")),
            "google_maps_cid": row.get("google_maps_cid", "").strip(),
            "email": row.get("email", "").strip(),
        },
        "primary_contact": get_primary_contact(row),
        "secondary_links": get_secondary_links(row),
        "scores": {
            "contactability": contactability_score(row),
            "visibility": visibility_score(row),
            "completeness": completeness_score(row),
        },
        "badges": get_badges(row),
        "intents": semantic["groups"],
        "discovery_groups": semantic["groups"],
        "semantic_tags": semantic["tags"],
        "semantic_attributes": semantic["attributes"],
        "search_synonyms": semantic["search_synonyms"],
        "semantic_review_state": semantic["review_state"],
        "description_facts": description_facts(row, enrich) if is_auto_description(row.get("description_full", "")) else None,
        "description": row.get("description_full", "").strip()[:500],
        "verified_date": row.get("verified_date", "").strip(),
        "provenance_summary": provenance_index().summary(row),
        "freshness_state": freshness.assess(
            row,
            provenance_index().capture_dates(row.get("google_maps_cid", "").strip()),
            today=build_today(),
        ).worst,
        "claim": {"status": "unclaimed"},
        "rating": enrich.get("rating"),
        "maps_address": enrich.get("address"),
        "subcategory": enrich.get("subcategory"),
        "check_in": enrich.get("check_in"),
        "check_out": enrich.get("check_out"),
        "amenities": infer_amenities(row, enrich.get("amenities", []), verified_amenities),
        "attributes": verified_attributes.get("attributes", []),
        "attribute_meta": {
            "capturedAt": verified_attributes.get("capturedAt", ""),
            "detectedGoogleName": verified_attributes.get("detectedGoogleName"),
        },
        "weekly_hours": verified_hours.get("weeklyHours", {}),
        "hours_meta": {
            "capturedAt": verified_hours.get("capturedAt", ""),
            "timezone": verified_hours.get("timezone", "America/Costa_Rica"),
            "completeness": verified_hours.get("completeness", "partial"),
        },
        "prices": enrich.get("prices", [])[:3],
        "open_status": enrich.get("open_status"),
        "hours": enrich.get("hours"),
        "plus_code": enrich.get("plus_code", ""),
        "cuisine": enrich.get("cuisine", ""),
    }
    return business


def public_business_summary(biz, t=None):
    """Return only fields needed by the public directory list/map UI."""
    return {
        "slug": biz["slug"],
        "name": biz["name"],
        "category": biz["category"],
        "category_label": viewmodels.category_label(biz["category"], t),
        "area": biz["area"],
        "lat": biz["lat"],
        "lng": biz["lng"],
        "distance_km": biz["distance_km"],
        "status": biz["status"],
        "channels": {
            "phone": bool(biz["channels"]["phone"]),
            "whatsapp": bool(biz["channels"]["whatsapp"]),
            "instagram": bool(biz["channels"]["instagram"]),
            "website": bool(biz["channels"]["website"]),
            "booking_url": bool(biz["channels"]["booking_url"]),
            "google_maps_cid": bool(biz["channels"]["google_maps_cid"]),
        },
        "primary_contact": {"type": biz["primary_contact"]["type"], "label": biz["primary_contact"]["label"]},
        "scores": biz["scores"],
        "badges": biz["badges"],
        "intents": biz["intents"],
        "discovery_groups": biz.get("discovery_groups", biz.get("intents", [])),
        "semantic_tags": biz.get("semantic_tags", []),
        "semantic_attributes": biz.get("semantic_attributes", []),
        "search_synonyms": biz.get("search_synonyms", []),
        "description": viewmodels.describe(biz, t),
        "rating": biz["rating"],
    }


CATEGORY_LABELS = {
    "hostel": "Hostel",
    "hotel": "Hotel",
    "nightlife": "Nightlife",
    "real_estate": "Real estate",
    "restaurant": "Restaurant",
    "services": "Services",
    "shopping": "Shopping",
    "tour_company": "Tours",
    "transport": "Transport",
    "vacation_rental": "Vacation rental",
    "wellness": "Wellness",
}


def category_label(category):
    key = (category or "").strip().lower()
    return CATEGORY_LABELS.get(key, key.replace("_", " ").title() or "Other")


DEFAULT_LANGUAGE = "en"
PRODUCTION_BASE_URL = "https://www.whappin.com"


def generate_profile_qr_codes(businesses):
    """Generate one print-ready QR image that opens each business profile."""
    qr_dir = OUTPUT_DIR / "qr"
    qr_dir.mkdir(parents=True, exist_ok=True)
    for biz in businesses:
        profile_url = f"{PRODUCTION_BASE_URL}/businesses/{biz['slug']}.html"
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(profile_url)
        qr.make(fit=True)
        image = qr.make_image(fill_color="#18382b", back_color="#ffffff")
        image = image.resize((300, 300), Image.Resampling.NEAREST)
        image.save(qr_dir / f"{biz['slug']}.png", "PNG", dpi=(300, 300))


def generate_deployment_wrapper():
    """Create the minimal repository-site root files not generated by the main build."""
    release_root = REPO_DIR / "release"
    if release_root != OUTPUT_DIR:
        return
    (release_root / ".nojekyll").write_text("", encoding="utf-8")
    (release_root / "CNAME").write_text("www.whappin.com\n", encoding="utf-8")
    (release_root / "404.html").write_text("""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/x-icon" href="../static/favicon.ico"><link rel="icon" type="image/png" sizes="32x32" href="../static/favicon-32x32.png"><link rel="icon" type="image/png" sizes="16x16" href="../static/favicon-16x16.png"><link rel="apple-touch-icon" href="../static/apple-touch-icon.png">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<link rel="stylesheet" href="static/tokens.css"><link rel="stylesheet" href="static/styles.css">
<meta name="robots" content="noindex"><title>Page not found — Whappin Puerto Viejo</title></head>
<body><main class="container"><div class="no-results"><h1>Page not found</h1><p>The place you requested is not available.</p><p><a href="./">Return to the directory</a></p></div></main></body></html>""", encoding="utf-8")


CAT_SHORTCUT_KEYS = [
    ("eat", "eat"), ("stay", "stay"), ("things-to-do", "tour"), ("services", "services"),
    ("shopping", "shopping"), ("wellness", "wellness"), ("nightlife", "nightlife"),
    ("transport", "transport"),
]


_JINJA_ENV = None


def jinja_env():
    """Lazily build the template environment.

    Autoescaping is on: values are escaped unless explicitly marked safe, which
    replaces per-call-site html.escape() discipline with a default that is safe
    when someone forgets.
    """
    global _JINJA_ENV
    if _JINJA_ENV is None:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        _JINJA_ENV = Environment(
            loader=FileSystemLoader(str(BASE_DIR / "templates")),
            autoescape=select_autoescape(default_for_string=True, default=True),
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=False,
        )
    return _JINJA_ENV


def render_index_html(businesses, metrics, language=DEFAULT_LANGUAGE):
    t = i18n.translator(language)
    counts = {}
    for business in businesses:
        for group in business["discovery_groups"]:
            counts[group] = counts.get(group, 0) + 1
    tiles = [
        {"key": key, "label": t(f"home.cat_{i18n_key}"), "count": counts.get(key, 0)}
        for key, i18n_key in CAT_SHORTCUT_KEYS
    ]
    prefix = t.path_prefix
    return jinja_env().get_template("index.html.j2").render(
        t=t,
        lang=language,
        languages=i18n.language_switch_links("index.html", language),
        alternates=i18n.alternate_links("", PRODUCTION_BASE_URL),
        canonical=f"{PRODUCTION_BASE_URL}/{prefix}",
        asset_prefix="../" if prefix else "",
        category_tiles=tiles,
        generated=metrics["generated"],
        taxonomy_version=TAXONOMY_VERSION,
    )

def render_business_html(biz, language=DEFAULT_LANGUAGE):
    t = i18n.translator(language)
    page = viewmodels.business_page(biz, TAXONOMY_VERSION, t)
    report_url = (
        "https://github.com/skinnerboxentertainment/mekatelyu/issues/new?"
        f"template=business_correction.md&title={quote('Correction: ' + biz['name'])}"
    )
    page_path = f"businesses/{biz['slug']}.html"
    return jinja_env().get_template("business.html.j2").render(
        page=page, icons=ICONS, report_url=report_url,
        t=t, lang=language,
        languages=i18n.language_switch_links(page_path, language),
        alternates=i18n.alternate_links(page_path, PRODUCTION_BASE_URL),
        canonical=f"{PRODUCTION_BASE_URL}/{t.path_prefix}{page_path}",
        # static/ and qr/ are shared at the site root; a language-prefixed tree
        # sits one level deeper, so it needs an extra step up.
        asset_prefix="../" if t.is_default else "../../",
    )


def render_invest_page(metrics):
    total = metrics["total"]
    with_cid = metrics["with_cid"]
    with_wa = metrics["with_whatsapp"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/x-icon" href="../static/favicon.ico"><link rel="icon" type="image/png" sizes="32x32" href="../static/favicon-32x32.png"><link rel="icon" type="image/png" sizes="16x16" href="../static/favicon-16x16.png"><link rel="apple-touch-icon" href="../static/apple-touch-icon.png">
<title>Invest in Whappin Puerto Viejo</title>
<meta name="description" content="Support a locally-built business directory for Puerto Viejo, Costa Rica — connecting tourists and locals to every business in town.">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<link rel="canonical" href="https://www.whappin.com/invest/">
<link rel="stylesheet" href="../static/tokens.css">
<link rel="stylesheet" href="../static/styles.css">
<link rel="stylesheet" href="../static/invest.css">
</head>
<body class="invest-page">
<h1>Whappin Puerto Viejo</h1>
<p class="subtitle">A community-built business directory for Puerto Viejo de Talamanca, Costa Rica. We're raising $5,000 to keep building.</p>

<div class="stat-row">
<div class="stat"><span class="stat-num">{total}</span><span class="stat-label">Businesses listed</span></div>
<div class="stat"><span class="stat-num">{with_cid}</span><span class="stat-label">Google Maps IDs</span></div>
<div class="stat"><span class="stat-num">{with_wa}</span><span class="stat-label">WhatsApp routes</span></div>
<div class="stat"><span class="stat-num">Live</span><span class="stat-label">whappin.com</span></div>
</div>

<h2>Why this matters</h2>
<p>
Puerto Viejo has no central directory. Tourists bounce between Google Maps, TripAdvisor, Facebook, Instagram, and word of mouth. Businesses have no unified digital presence — many don't even have a website. Whappin fixes that: one place, every business, opt-out by default, works on any phone, zero infrastructure costs.
</p>
<p>
This is a mitzvah for the community. We want to be good stewards of better awareness for the town — helping tourists find what they need, helping locals promote what they offer, and helping everyone navigate Puerto Viejo with confidence.
</p>

<h2>What we've built so far</h2>
<ul>
<li>737 entity-resolved business profiles with 34 data fields each</li>
<li>726 Google Maps CIDs mapped (98% coverage)</li>
<li>175 validated WhatsApp routes</li>
<li>One QR code per business — print-ready for doors, menus, counters</li>
<li>Full-text search, category/area filters, interactive map, semantic tags</li>
<li>Mobile-first responsive design — works on any device</li>
<li>Continuous deployment via GitHub Actions, 54 automated tests</li>
<li>Live at <a href="https://www.whappin.com/">www.whappin.com</a> — go see it</li>
</ul>

<h2>The opportunity</h2>
<p>
Costa Rica sees 5M+ tourists annually. Puerto Viejo is the Caribbean coast's #2 destination. There is no dominant local directory for any CR town. Whappin is first to market with a complete, verified dataset. The model is replicable to Tamarindo, Manuel Antonio, Santa Teresa, La Fortuna, Monteverde — every town with a tourism economy.
</p>

<h2>The ask</h2>
<p>
<strong>$5,000 by end of 2026</strong> — structured as a sponsorship or revenue-share agreement. This covers the next phase of development: premium listing infrastructure, QR affiliate network, WhatsApp concierge tools, and porting the scanner to a second town. We're building something that serves the community and has real revenue potential.
</p>

<p><strong>Use of funds:</strong></p>
<table class="funds-table">
<tr><td>QR affiliate network development</td><td>$1,500</td></tr>
<tr><td>WhatsApp concierge MVP</td><td>$1,000</td></tr>
<tr><td>Pitch deck, legal, and business setup</td><td>$1,000</td></tr>
<tr><td>Scanner port to second town</td><td>$500</td></tr>
<tr><td>Domain, hosting, and operations (3 years)</td><td>$500</td></tr>
<tr><td>Sustainable living while building</td><td>$500</td></tr>
</table>

<div class="cta-box">
<h3>Interested?</h3>
<p>Submit an inquiry or send us an email. We'll respond within 48 hours.</p>
<p>
<a href="https://github.com/skinnerboxentertainment/mekatelyu/issues/new?template=investor-inquiry.md" class="btn" target="_blank" rel="noopener">Submit inquiry</a>
<a href="mailto:ideaguyinteractive@gmail.com?subject=Investing%20in%20Whappin%20Puerto%20Viejo" class="btn btn-outline" target="_blank" rel="noopener">Email us</a>
</p>
</div>

<h2>Team</h2>
<p>
Oscar AF — builder, traveler, community organizer. Built the entire platform: data pipeline, web app, enrichment automation, CI/CD, audit framework, and deployment infrastructure. This project is a labor of love for a town that deserves a better way to connect.
</p>

<div class="footer">
<p><a href="https://www.whappin.com/">Whappin Puerto Viejo</a> &middot; <a href="https://github.com/skinnerboxentertainment/mekatelyu">GitHub</a> &middot; Built in Costa Rica</p>
</div>
</body>
</html>"""


def main():
    if OUTPUT_DIR == REPO_DIR:
        raise RuntimeError(f"Refusing unsafe output directory: {OUTPUT_DIR}")
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    biz_dir = OUTPUT_DIR / "businesses"
    biz_dir.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "static").mkdir(parents=True, exist_ok=True)

    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        return

    businesses = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            biz = build_business(row)
            businesses.append(biz)

    businesses.sort(key=lambda b: b["name"].lower())
    businesses = dedup_slugs(businesses)

    categories = {}
    areas = {}
    for b in businesses:
        cat = b["category"] or "Uncategorized"
        ar = b["area"] or "Unknown"
        categories[cat] = categories.get(cat, 0) + 1
        areas[ar] = areas.get(ar, 0) + 1

    metrics = {
        "total": len(businesses),
        "with_whatsapp": sum(1 for b in businesses if b["channels"]["whatsapp"]),
        "with_instagram": sum(1 for b in businesses if b["channels"]["instagram"]),
        "with_instagram_verified": sum(1 for b in businesses if b["channels"]["instagram_verified"]),
        "with_phone": sum(1 for b in businesses if b["channels"]["phone"]),
        "with_website": sum(1 for b in businesses if b["channels"]["website"]),
        "with_cid": sum(1 for b in businesses if b["channels"]["google_maps_cid"]),
        "with_facebook": sum(1 for b in businesses if b["channels"]["facebook_url"]),
        "with_booking": sum(1 for b in businesses if b["channels"]["booking_url"]),
        "with_email": sum(1 for b in businesses if b["channels"]["email"]),
        "categories": dict(sorted(categories.items(), key=lambda x: -x[1])),
        "areas": dict(sorted(areas.items(), key=lambda x: -x[1])),
        "semantic_facets": {
            tag: sum(1 for b in businesses if tag in b["semantic_tags"] or tag in b["semantic_attributes"])
            for tag in sorted(TAG_LABELS)
            if any(tag in b["semantic_tags"] or tag in b["semantic_attributes"] for b in businesses)
        },
        "generated": build_date(),
    }

    print(f"Building Whappin Puerto Viejo — {len(businesses)} businesses")

    generate_profile_qr_codes(businesses)
    print(f"  qr/ — {len(businesses)} profile QR codes")

    # One page tree per language. English is un-prefixed and keeps the existing
    # URLs, because 736 printed QR codes point at /businesses/<slug>.html and
    # those stickers are already on doors around town.
    languages = i18n.available_languages()
    for language in languages:
        root = OUTPUT_DIR if language == DEFAULT_LANGUAGE else OUTPUT_DIR / language
        pages_dir = root / "businesses"
        pages_dir.mkdir(parents=True, exist_ok=True)
        for biz in businesses:
            page_html = render_business_html(biz, language)
            with open(pages_dir / f"{biz['slug']}.html", "w", encoding="utf-8") as f:
                f.write(page_html)
        with open(root / "index.html", "w", encoding="utf-8") as f:
            f.write(render_index_html(businesses, metrics, language))
        label = "" if language == DEFAULT_LANGUAGE else f"{language}/"
        print(f"  {label}businesses/ — {len(businesses)} pages + index ({language})")

    def directory_payload(language, extra_summaries=()):
        """The client payload for one language.

        Result cards and the text search read from this, so a single English
        payload would leave search results and descriptions in English on a
        Spanish page even though the surrounding chrome is translated.
        """
        translate = i18n.translator(language)
        built = [public_business_summary(b, translate) for b in businesses]
        built.extend(extra_summaries)
        body = (
            "const BUSINESSES=" + json.dumps(built, ensure_ascii=False, separators=(",", ":")) + ";\n"
            "const CATEGORIES=" + json.dumps(metrics["categories"], ensure_ascii=False, separators=(",", ":")) + ";\n"
            "const SEMANTIC_FACETS=" + json.dumps(metrics["semantic_facets"], ensure_ascii=False, separators=(",", ":")) + ";\n"
            "const SEMANTIC_LABELS=" + json.dumps(TAG_LABELS, ensure_ascii=False, separators=(",", ":")) + ";\n"
            "const AREAS=" + json.dumps(metrics["areas"], ensure_ascii=False, separators=(",", ":")) + ";\n"
        )
        return built, body

    def write_directory_payloads(extra_summaries=()):
        written = None
        for language in i18n.available_languages():
            built, body = directory_payload(language, extra_summaries)
            if language == DEFAULT_LANGUAGE:
                written = built
            (OUTPUT_DIR / "static" / f"directory-data-{language}.js").write_text(body, encoding="utf-8")
        return written

    write_directory_payloads()

    # Per-language UI strings for the client scripts. A separate file per
    # language rather than an inline block, because the CSP allows only
    # 'self' scripts — an inline <script> would be blocked.
    for language in i18n.available_languages():
        strings = i18n.load_strings(language)
        payload = (
            "const UI_STRINGS=" + json.dumps(strings, ensure_ascii=False, separators=(",", ":")) + ";\n"
            # The client's staleness threshold comes from the freshness policy,
            # so the two cannot drift apart into disagreeing about when a
            # schedule stops being trustworthy.
            f"const LIVE_STATUS_MAX_AGE_DAYS={freshness.LIVE_STATUS_MAX_AGE_DAYS};\n"
        )
        (OUTPUT_DIR / "static" / f"ui-{language}.js").write_text(payload, encoding="utf-8")

    static_src = STATIC_DIR / "app.js"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "app.js")
    static_src = STATIC_DIR / "detail.js"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "detail.js")
    static_src = STATIC_DIR / "tokens.css"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "tokens.css")
    static_src = STATIC_DIR / "invest.css"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "invest.css")
    static_src = STATIC_DIR / "styles.css"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "styles.css")
    static_src = STATIC_DIR / "community.css"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "community.css")
    for fav in ["favicon.ico", "favicon-16x16.png", "favicon-32x32.png", "apple-touch-icon.png"]:
        src = STATIC_DIR / fav
        if src.exists():
            shutil.copy2(src, OUTPUT_DIR / "static" / fav)
    vendor_src = STATIC_DIR / "vendor"
    if vendor_src.exists():
        dst = OUTPUT_DIR / "static" / "vendor"
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(vendor_src, dst)
    print("  static/ — directory-data.js, tokens.css, invest.css, community.css, app.js, detail.js, styles.css, favicons, vendor/")

    urls = [PRODUCTION_BASE_URL + "/"] + [PRODUCTION_BASE_URL + f"/businesses/{b['slug']}.html" for b in businesses]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{url}</loc></url>\n" for url in urls)
    sitemap += "</urlset>\n"
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUTPUT_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {PRODUCTION_BASE_URL}/sitemap.xml\n", encoding="utf-8")
    print("  robots.txt + sitemap.xml")

    invest_dir = OUTPUT_DIR / "invest"
    invest_dir.mkdir(parents=True, exist_ok=True)
    (invest_dir / "index.html").write_text(render_invest_page(metrics), encoding="utf-8")
    print("  invest/ — angel investment page")

    orgs = load_organizations(BASE_DIR / "data" / "organizations.json")
    if orgs:
        org_summaries = []
        for org in orgs:
            html = render_organization_html(org)
            slug = org["slug"]
            (biz_dir / f"{slug}.html").write_text(html, encoding="utf-8")
            org_summaries.append(public_org_summary(org))
            print(f"  businesses/{slug}.html — {org['name']}")
        # Rewrite every language's payload so community partners appear in the
        # directory listing alongside businesses.
        write_directory_payloads(org_summaries)
        urls = [PRODUCTION_BASE_URL + "/"] + [PRODUCTION_BASE_URL + f"/businesses/{b['slug']}.html" for b in businesses + org_summaries]
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        sitemap += "".join(f"  <url><loc>{url}</loc></url>\n" for url in urls)
        sitemap += "</urlset>\n"
        (OUTPUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
        print(f"  organizations/ — {len(orgs)} community partners")

    generate_deployment_wrapper()
    print("  release root — redirect, 404, robots, .nojekyll")

    fav_root = STATIC_DIR / "favicon.ico"
    if fav_root.exists():
        shutil.copy2(fav_root, OUTPUT_DIR / "favicon.ico")
    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

