import csv
import json
import hashlib
import html
import re
import os
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import qrcode
from PIL import Image
try:
    from .semantic_taxonomy import PRIMARY_CATEGORY_TAGS, TAG_LABELS, TAXONOMY_VERSION, classify_record, semantic_key
except ImportError:  # Direct execution: python paradisio_app/build.py
    from semantic_taxonomy import PRIMARY_CATEGORY_TAGS, TAG_LABELS, TAXONOMY_VERSION, classify_record, semantic_key

AMENITY_MAP = {
    "wi-fi gratis": "Free Wi-Fi", "wifi": "Free Wi-Fi", "wi-fi": "Free Wi-Fi",
    "incluye wi-fi": "Free Wi-Fi",
    "incluye wi-fi y estacionamiento": "Free Wi-Fi \u00b7 Free parking",
    "incluye desayuno, wi-fi y estacionamiento": "Free breakfast \u00b7 Free Wi-Fi \u00b7 Free parking",
    "incluye desayuno y estacionamiento": "Free breakfast \u00b7 Free parking",
    "incluye desayuno": "Free breakfast", "desayuno incluido": "Free breakfast",
    "desayuno": "Breakfast available", "desayuno pago": "Paid breakfast",
    "estacionamiento gratuito": "Free parking",
    "aire acondicionado": "Air conditioning",
    "se permiten mascotas": "Pet friendly",
    "accesible": "Wheelchair accessible",
    "piscina": "Pool", "piscina al aire libre": "Outdoor pool",
    "piscina cubierta / aire libre": "Indoor/outdoor pool",
    "gimnasio": "Gym",
    "transporte desde/hacia el aeropuerto": "Airport shuttle",
    "cocina en todas las habitaciones": "In-room kitchen",
    "cocina en algunas habitaciones": "Kitchen in some rooms",
    "cocina": "Kitchen",
    "bar": "Bar", "bar restaurante": "Bar & restaurant",
    "spa": "Spa", "spa de masajes": "Massage spa",
    "libre de humo": "Smoke-free",
    "centro de negocios": "Business center",
    "cocina latinoamericana": "Latin American cuisine",
    "cocina panasi\u00e1tica": "Pan-Asian cuisine",
    "bed & breakfast": "Bed & breakfast",
    "espacio": "Outdoor space", "terraza": "Terrace",
    "restobar": "Restobar",
    "incluye desayuno, wifi y estacionamiento": "Free breakfast \u00b7 Free Wi-Fi \u00b7 Free parking",
    "incluye wifi y estacionamiento": "Free Wi-Fi \u00b7 Free parking",
    "incluye desayuno y wifi": "Free breakfast \u00b7 Free Wi-Fi",
    "wifi gratis": "Free Wi-Fi",
    "incluye desayuno y wi-fi": "Free breakfast \u00b7 Free Wi-Fi",
}

AMENITY_NOISE = {"puro", "puerto", "chao", "physis", "azul", "espagueti", "beach gym",
                 "secret garden", "hotel piscina", "el jardin", "restaurante",
                 "internet", "incluye"}


def normalize_amenities(raw_list):
    normalized = []
    seen = set()
    for a in raw_list:
        key = a.lower().strip()
        if any(k in key for k in AMENITY_NOISE):
            continue
        eng = AMENITY_MAP.get(key)
        if eng and eng not in seen:
            normalized.append(eng)
            seen.add(eng)
    return normalized


def is_auto_description(text):
    if not text:
        return True
    text = text.strip()
    return len(text) < 100 and re.match(r'^[A-Z][a-zA-Z0-9\s\-\'\u00c0-\u024f]+ is (a|an) ', text.strip(), re.I) is not None


def generate_description(row, enrich):
    cat_label = row.get("category", "").strip().replace("_", " ").title()
    area = row.get("area", "").strip() or "Puerto Viejo"
    rating = enrich.get("rating") if enrich else None
    parts = [f"{cat_label} in {area}."]
    if rating:
        parts.append(f"Rated {rating}/5 on Google Maps.")
    phone = row.get("phone", "").strip()
    website = row.get("website", "").strip()
    instagram = row.get("instagram_handle", "").strip()
    if phone or website or instagram:
        parts.append("Contact for hours and availability.")
    return " ".join(parts)

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
REPO_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.environ.get("PARADISIO_OUTPUT_DIR", REPO_DIR / "release")).resolve()
CSV_PATH = BASE_DIR.parent / "pv_master_unified.csv"
MAPS_ENRICH_PATH = BASE_DIR / "data" / "maps_parsed_v3.json"
SEMANTIC_TAXONOMY_PATH = BASE_DIR / "data" / "semantic_taxonomy.json"
LOCALES_DIR = BASE_DIR / "data" / "locales"


def load_locales():
    locales = {}
    for path in LOCALES_DIR.glob("*.json"):
        lang = path.stem
        with open(path, encoding="utf-8") as f:
            locales[lang] = json.load(f)
    return locales


LOCALES = load_locales()
LOCALE_NAMES = {lang: data.get("lang.name_en", lang) for lang, data in LOCALES.items()}


NAV_PAGES = {"directory": "Directory"}


def nav_html(current, depth=0):
    prefix = "../" if depth > 0 else ""
    links = f'<a href="{prefix}index.html" class="site-logo">Whappin Puerto Viejo</a>'
    for key, label in NAV_PAGES.items():
        href = {"directory": f"{prefix}index.html"}.get(key, "#")
        active = "nav-active" if key == current else ""
        en = {"directory": "Directory"}.get(key, label)
        links += f'<a href="{href}" class="{active}">{en}</a>'
    return f'<nav class="site-nav" aria-label="Primary navigation">{links}</nav>'


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
        if "fields" in r and r["fields"]:
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

WHATSAPP_TEMPLATE = "Hola {name}, vi su pagina en Paradisio. Estan abiertos hoy? Me gustaria saber mas sobre sus servicios. Gracias."

LOCATION_TOKENS = {"puerto viejo", "limon", "limon", "costa rica", "playa negra", "playa cocles",
                   "playa chiquita", "punta uva", "playa punta uva", "cahuita", "manzanillo",
                   "hone creek", "bribri", "sixaola", "gandoca", "cocles"}


def clean_display_name(raw_name, area):
    name = raw_name.strip()
    if not name:
        return name
    # If name has " - " separator, check if right side is location info
    if " - " in name:
        left, right = name.split(" - ", 1)
        # If the right side contains location tokens or is the area, strip it
        right_lower = right.lower()
        if any(t in right_lower for t in LOCATION_TOKENS) or area.lower() in right_lower:
            name = left.strip()
            # Re-check for nested " - " in the remaining name
            if " - " in name:
                left2, right2 = name.split(" - ", 1)
                if any(t in right2.lower() for t in LOCATION_TOKENS) or area.lower() in right2.lower():
                    name = left2.strip()
    # Strip trailing "Costa Rica" after removing dash section
    name = re.sub(r"[,–—\- ]*Costa Rica$", "", name, flags=re.IGNORECASE).strip()
    # Strip trailing location suffixes via comma split
    parts = re.split(r"\s*,\s*", name)
    if len(parts) > 1:
        suffix = parts[-1].strip().lower()
        if suffix in LOCATION_TOKENS or suffix == area.lower():
            name = ",".join(parts[:-1]).strip()
    # Clean any remaining trailing separators
    name = re.sub(r"[\s,–—-]+$", "", name).strip()
    return name if name else raw_name.strip()


def slugify(name, area):
    s = f"{name}-{area}"
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s[:80]


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
    raw = f"{row.get('business_name','')}|{row.get('google_maps_cid','')}|{row.get('phone','')}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def normalize_phone(raw):
    if not raw:
        return ""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 8:
        digits = "506" + digits
    if re.fullmatch(r"\d{10,15}", digits):
        return "+" + digits
    return ""


def safe_external_url(raw):
    value = (raw or "").strip()
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment))


def safe_instagram_handle(raw):
    handle = (raw or "").strip().lstrip("@")
    return handle if re.fullmatch(r"[A-Za-z0-9._]{1,30}", handle) else ""


def has_whatsapp(row):
    """Return an explicit WhatsApp destination in international digits.

    Ordinary phone numbers are deliberately not inferred as WhatsApp-capable.
    """
    raw = row.get("whatsapp", "").strip()
    if not raw:
        return ""
    match = re.search(r"(?:phone=|wa\.me/)(\d{8,15})", raw)
    digits = match.group(1) if match else re.sub(r"\D", "", raw)
    if len(digits) == 8:
        digits = "506" + digits
    if not re.fullmatch(r"\d{10,15}", digits):
        return ""
    return "+" + digits


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


def get_intents(category):
    mapping = {
        "hotel": ["stay"],
        "vacation_rental": ["stay"],
        "hostel": ["stay"],
        "restaurant": ["eat"],
        "tour_company": ["tour"],
        "shopping": ["shopping"],
        "services": ["services"],
        "real_estate": ["services"],
        "wellness": ["wellness"],
        "nightlife": ["nightlife"],
        "transport": ["transport"],
    }
    return mapping.get(category.lower().strip(), ["other"])


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


MAPS_CACHE = None
SEMANTIC_CACHE = None


def maps_data(cid):
    global MAPS_CACHE
    if MAPS_CACHE is None:
        MAPS_CACHE = load_maps_enrich()
    return MAPS_CACHE.get(cid, {})


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
        "description": generate_description(row, enrich) if is_auto_description(row.get("description_full", "")) else row.get("description_full", "").strip()[:500],
        "verified_date": row.get("verified_date", "").strip(),
        "claim": {"status": "unclaimed"},
        "rating": enrich.get("rating"),
        "maps_address": enrich.get("address"),
        "subcategory": enrich.get("subcategory"),
        "check_in": enrich.get("check_in"),
        "check_out": enrich.get("check_out"),
        "amenities": normalize_amenities(enrich.get("amenities", [])),
        "prices": enrich.get("prices", [])[:3],
        "open_status": enrich.get("open_status"),
        "hours": enrich.get("hours"),
        "plus_code": enrich.get("plus_code", ""),
        "cuisine": enrich.get("cuisine", ""),
    }
    return business


def public_business_summary(biz):
    """Return only fields needed by the public directory list/map UI."""
    return {
        "slug": biz["slug"],
        "name": biz["name"],
        "category": biz["category"],
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
        "description": biz["description"],
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


def status_html(status):
    key = (status or "").strip().lower()
    labels = {
        "closed": "Closed",
        "permanently_closed": "Closed",
        "needs_verification": "Information needs review",
    }
    label = labels.get(key)
    if not label:
        return ""
    return f'<span class="biz-status status-{key}">{label}</span>'


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
    if OUTPUT_DIR != release_root:
        return
    (release_root / ".nojekyll").write_text("", encoding="utf-8")
    (release_root / "404.html").write_text(f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<link rel="stylesheet" href="static/tokens.css"><link rel="stylesheet" href="static/styles.css">
<meta name="robots" content="noindex"><title>Page not found — Whappin Puerto Viejo</title></head>
<body><main class="container"><div class="no-results"><h1>Page not found</h1><p>The place you requested is not available.</p><p><a href="./">Return to the directory</a></p></div></main></body></html>""", encoding="utf-8")


CAT_SHORTCUTS = [
    ("eat", "Eat", "Comer"),
    ("stay", "Stay", "Hospedarse"),
    ("things-to-do", "Things to Do", "Actividades"),
    ("services", "Services", "Servicios"),
    ("shopping", "Shops", "Tiendas"),
    ("wellness", "Wellness", "Bienestar"),
    ("nightlife", "Nightlife", "Vida Nocturna"),
    ("transport", "Transport", "Transporte"),
]


def cat_grid_html(businesses):
    counts = {}
    for business in businesses:
        for group in business["discovery_groups"]:
            counts[group] = counts.get(group, 0) + 1

    tiles = ""
    for key, en, es in CAT_SHORTCUTS:
        c = counts.get(key, 0)
        tiles += f'<a href="#" class="cat-tile" data-category="{key}"><div data-i18n="home.cat_{key}">{en}</div><span class="cat-count">{c} businesses</span></a>'
    return f'<div class="cat-grid">{tiles}</div>'


def render_index_html(businesses, metrics):
    total = metrics["total"]
    with_wp = metrics["with_whatsapp"]
    with_ig = metrics["with_instagram"]
    with_phone = metrics["with_phone"]
    with_cid = metrics["with_cid"]
    date = metrics["generated"]

    nav = nav_html("directory", depth=0)
    cat_grid = cat_grid_html(businesses)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Whappin Puerto Viejo</title>
<meta name="description" content="Find trusted places across Puerto Viejo.">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self' https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests">
<link rel="canonical" href="https://www.whappin.com/">
<meta property="og:title" content="Whappin Puerto Viejo">
<meta property="og:description" content="Find trusted places across Puerto Viejo.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://www.whappin.com/">
<link rel="stylesheet" href="static/tokens.css?v={TAXONOMY_VERSION}">
<link rel="stylesheet" href="static/styles.css?v={TAXONOMY_VERSION}">
<link rel="stylesheet" href="static/vendor/leaflet/leaflet.css">
<link rel="stylesheet" href="static/vendor/leaflet/MarkerCluster.css">
<link rel="stylesheet" href="static/vendor/leaflet/MarkerCluster.Default.css">
</head>
<body>
{nav}
<main class="container">
<header class="masthead">
<h1>Whappin Puerto Viejo</h1>
<p class="tagline">Powered by Paradisio</p>
<p class="subtitle">Find trusted places across Puerto Viejo.</p>
</header>
<div class="controls">
<label class="sr-only" for="search">Search businesses</label>
<input type="search" id="search" class="search-input" placeholder="Search by name, type, quality, or area" autofocus>
<div class="view-toggle">
<button id="view-list" class="view-btn active" aria-pressed="true">List</button>
<button id="view-map" class="view-btn" aria-pressed="false">Map</button>
</div>
<div class="filters">
<label class="sr-only" for="category-filter">Category</label>
<select id="category-filter" class="filter-select" aria-label="Category">
<option value="">All categories</option>
</select>
<label class="sr-only" for="tag-filter">Type or quality</label>
<select id="tag-filter" class="filter-select" aria-label="Type or quality">
<option value="">Any type or quality</option>
</select>
<label class="sr-only" for="area-filter">Area</label>
<select id="area-filter" class="filter-select" aria-label="Area">
<option value="">All areas</option>
</select>
<label class="sr-only" for="channel-filter">Contact method</label>
<select id="channel-filter" class="filter-select" aria-label="Contact method">
<option value="">Any contact</option>
<option value="whatsapp">Has WhatsApp</option>
<option value="instagram">Has Instagram</option>
<option value="phone">Has phone</option>
<option value="website">Has website</option>
<option value="booking">Has Booking.com</option>
<option value="maps">On Google Maps</option>
</select>
<label class="sr-only" for="sort-filter">Sort results</label>
<select id="sort-filter" class="filter-select" aria-label="Sort results">
<option value="name">Sort: Name</option>
<option value="contactability">Sort: Best contact</option>
<option value="completeness">Sort: Most complete</option>
</select>
</div>
{cat_grid}
<div id="stats-line" class="stats-line"></div>
<div id="filter-chips" class="filter-chips"></div>
</div>
<div id="results" class="results">
<div class="loading">Loading directory...</div>
</div>
<div id="load-more" class="load-more"></div>
<div id="map-container" class="map-view"></div>
<footer class="footer">
<p>Whappin Puerto Viejo &middot; Directory updated {date}</p>
<p><a href="https://github.com/skinnerboxentertainment/mekatelyu/issues/new?template=business_correction.md" target="_blank" rel="noopener">Report incorrect information</a></p>
</footer>
</main>
<script src="static/directory-data.js?v={TAXONOMY_VERSION}"></script>
<script src="static/vendor/leaflet/leaflet.js"></script>
<script src="static/vendor/leaflet/leaflet.markercluster.js"></script>
<script src="static/app.js?v={TAXONOMY_VERSION}"></script>
</body>
</html>"""


def rating_html(biz):
    r = biz.get("rating")
    if r is None:
        return ""
    full = int(r)
    half = "&#189;" if r % 1 >= 0.3 else ""
    stars = "&#9733;" * full + half
    return f'<div class="biz-rating">{stars} {r}</div>'


def biz_addr(biz):
    parts = []
    a = biz.get("maps_address")
    if a and not a.startswith(("M", "F", "C")):
        parts.append(a)
    pc = biz.get("plus_code")
    if pc:
        parts.append(f'<span class="plus-code">{pc}</span>')
    if not parts and a:
        parts.append(a)
    return f'<div class="biz-addr">{" · ".join(parts)}</div>' if parts else ""


def clean_time(t):
    return t.replace("?", "").replace("\u202f", " ") if t else ""

def biz_hours(biz):
    parts = []
    os = biz.get("open_status")
    if os:
        clean = os.replace("\u202f", " ").replace("\u00a0", " ").strip()
        cls = "biz-open" if "abierto" in clean.lower() or "open" in clean.lower() else "biz-closed"
        parts.append(f'<span class="{cls}">{clean}</span>')
    hr = biz.get("hours")
    if hr:
        parts.append(f'<span class="biz-hours-line">{hr}</span>')
    ci = clean_time(biz.get("check_in"))
    co = clean_time(biz.get("check_out"))
    if ci and co:
        parts.append(f'<span class="biz-check">In {ci} / Out {co}</span>')
    elif ci:
        parts.append(f'<span class="biz-check">In {ci}</span>')
    elif co:
        parts.append(f'<span class="biz-check">Out {co}</span>')
    return f'<div class="biz-hours">{", ".join(parts)}</div>' if parts else ""


def biz_amenities(biz):
    am = biz.get("amenities", [])
    if not am:
        return ""
    chips = " ".join(f'<span class="amenity-chip">{a}</span>' for a in am[:6])
    return f'<div class="amenities">{chips}</div>'


def biz_semantic_facets(biz):
    facets = []
    primary_tag = PRIMARY_CATEGORY_TAGS.get((biz.get("category") or "").strip().lower())
    for tag in biz.get("semantic_tags", []) + biz.get("semantic_attributes", []):
        if tag == primary_tag or tag in facets:
            continue
        facets.append(tag)
    if not facets:
        return ""
    chips = " ".join(
        f'<span class="amenity-chip">{html.escape(TAG_LABELS.get(tag, tag.replace("-", " ").title()))}</span>'
        for tag in facets[:6]
    )
    return f'<div class="amenities semantic-facets" aria-label="Types and qualities">{chips}</div>'


def biz_prices(biz):
    prices = biz.get("prices", [])
    if not prices:
        return ""
    items = " ".join(f'<span class="price-chip">{p}</span>' for p in prices[:3])
    return f'<div class="biz-prices">{items}</div>'


def biz_freshness(biz):
    vd = biz.get("verified_date", "")
    if not vd:
        return ""
    return f'<div class="biz-freshness">Data captured {vd[:10]}</div>'


def render_premium_page():
    nav = nav_html("directory", depth=0)
    email = CLAIM_EMAIL
    sinpe = SINPE_PHONE
    bank = SINPE_BANK
    name = SINPE_NAME
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Premium Listings — Paradisio</title>
<link rel="stylesheet" href="static/tokens.css">
<link rel="stylesheet" href="static/styles.css">
</head>
<body>
{nav}
<div class="container premium-page">
<h1>Premium Listings</h1>
<p class="subtitle">Get more visibility, more calls, more bookings. SINPE Móvil payment — no credit card needed.</p>

<div class="premium-tiers">
  <div class="tier">
    <h2>Featured</h2>
    <div class="tier-price">$100 / year</div>
    <ul>
      <li>Featured placement in search results</li>
      <li>Priority listing in your category</li>
      <li>Monthly page view analytics</li>
      <li>Outbound click tracking</li>
      <li>"Premium" badge on your page</li>
      <li>Email support</li>
    </ul>
    <a href="#pay" class="primary-cta">Upgrade to Featured</a>
  </div>
  <div class="tier tier-pro">
    <h2>Pro</h2>
    <div class="tier-price">$200 / year</div>
    <ul>
      <li>Everything in Featured</li>
      <li>Custom QR sticker pack (10 stickers)</li>
      <li>WhatsApp auto-reply setup</li>
      <li>Instagram profile link on your page</li>
      <li>Featured in monthly email newsletter</li>
      <li>Priority support via WhatsApp</li>
    </ul>
    <a href="#pay" class="primary-cta">Upgrade to Pro</a>
  </div>
</div>

<div id="pay" class="payment-section">
<h2>Pay via SINPE Móvil</h2>
<p>Send the amount to the following SINPE Móvil account, then notify us so we can activate your listing.</p>

<div class="sinpe-details">
  <div class="sinpe-info">
    <strong>Recipient:</strong> {name}<br>
    <strong>Bank:</strong> {bank}<br>
    <strong>SINPE Móvil:</strong> <span class="sinpe-number">{sinpe}</span>
  </div>
</div>

<p class="payment-note">After sending payment, please <a href="claim.html?subject=Premium%20Payment">contact us</a> with your business name, the amount sent, and the date so we can activate your premium features within 24 hours.</p>
</div>
</div>
<footer class="footer">
<p><a href="index.html">&larr; Back to directory</a></p>
</footer>
</body>
</html>"""


def render_claim_page():
    nav = nav_html("directory", depth=0)
    email = CLAIM_EMAIL
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claim Your Business — Paradisio</title>
<link rel="stylesheet" href="static/tokens.css">
<link rel="stylesheet" href="static/styles.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" crossorigin="">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" crossorigin="">
</head>
<body>
{nav}
<div class="container claim-page">
<h1>Claim or Correct Your Business Listing</h1>
<p>Is your business listed on Paradisio? Fill out this form to claim ownership, update your hours, contact info, photos, or description. We review every submission.</p>

<form action="https://formsubmit.co/{email}" method="POST" class="claim-form">
  <input type="hidden" name="_subject" value="Paradisio claim/correction">
  <input type="hidden" name="_template" value="table">
  <input type="hidden" name="_captcha" value="true">

  <fieldset>
    <legend>Your Business</legend>
    <label>Business name *<br><input type="text" name="business_name" required placeholder="e.g. Amimodo Beach Rooms"></label>
    <label>Business area<br><input type="text" name="business_area" placeholder="e.g. Puerto Viejo, Playa Cocles"></label>
  </fieldset>

  <fieldset>
    <legend>Your Contact</legend>
    <label>Your name *<br><input type="text" name="claimant_name" required placeholder="Full name"></label>
    <label>Your email *<br><input type="email" name="claimant_email" required placeholder="you@example.com"></label>
    <label>Your phone<br><input type="tel" name="claimant_phone" placeholder="+506 8888 8888"></label>
    <label>Relationship to business<br>
      <select name="relationship">
        <option value="owner">Owner</option>
        <option value="manager">Manager</option>
        <option value="employee">Employee</option>
        <option value="other">Other</option>
      </select>
    </label>
  </fieldset>

  <fieldset>
    <legend>Corrections or Updates</legend>
    <p>Only fill in the fields you want to change:</p>
    <label>Phone<br><input type="tel" name="phone" placeholder="+506 2750 0000"></label>
    <label>WhatsApp<br><input type="tel" name="whatsapp" placeholder="+506 8888 8888"></label>
    <label>Website<br><input type="url" name="website" placeholder="https://example.com"></label>
    <label>Instagram<br><input type="text" name="instagram" placeholder="@yourhandle or https://instagram.com/..."></label>
    <label>Facebook<br><input type="url" name="facebook" placeholder="https://facebook.com/..."></label>
    <label>Opening hours<br><textarea name="hours" rows="2" placeholder="Mon-Fri 9am-5pm, Sat 10am-2pm"></textarea></label>
    <label>Description<br><textarea name="description" rows="3" placeholder="Short description of your business"></textarea></label>
    <label>Category<br>
      <select name="category">
        <option value="">— No change —</option>
        <option>Hotel</option>
        <option>Hostel</option>
        <option>Restaurant</option>
        <option>Tour Company</option>
        <option>Services</option>
        <option>Shopping</option>
        <option>Vacation Rental</option>
      </select>
    </label>
    <label>Additional notes<br><textarea name="notes" rows="3" placeholder="Anything else we should know?"></textarea></label>
  </fieldset>

  <button type="submit" class="primary-cta">Submit for Review</button>
  <p class="form-note">We'll review your submission and update the listing within 1-3 days.</p>
</form>
</div>
<footer class="footer">
<p><a href="index.html">&larr; Back to directory</a></p>
</footer>
</body>
</html>"""


def render_admin_page():
    """God's Eye dashboard — invoice tracking, revenue, system status."""
    nav = nav_html("directory", depth=0)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin Dashboard — Paradisio</title>
<link rel="stylesheet" href="static/tokens.css">
<link rel="stylesheet" href="static/styles.css">
<script>
const LOCALE_DATA = {json.dumps(LOCALES, ensure_ascii=False)};
</script>
<script src="static/i18n.js"></script>
<script src="static/modes.js"></script>
<script>
(function(){{ try {{ if(window.setParadisioMode) setParadisioMode('god'); }} catch(e){{ }} }})();
</script>
</head>
<body data-mode="god">
{nav}
<div class="container">
<h1>Admin Dashboard</h1>
<p class="subtitle">God's Eye view — revenue, invoices, system status.</p>
<p>Data is loaded from <code>data/invoices.json</code> and <code>data/metrics.json</code>.</p>
<div id="admin-content">
  <div class="loading">Loading admin data...</div>
</div>
</div>
<footer class="footer">
<p><a href="index.html">&larr; Back to directory</a></p>
</footer>
<script>
fetch('data/metrics.json').then(function(r){{ return r.json(); }}).then(function(m) {{
  document.getElementById('admin-content').innerHTML =
    '<div class="admin-grid">' +
    '<div class="admin-card"><h3>Total Businesses</h3><div class="admin-stat">' + m.total + '</div></div>' +
    '<div class="admin-card"><h3>With WhatsApp</h3><div class="admin-stat">' + m.with_whatsapp + '</div></div>' +
    '<div class="admin-card"><h3>With Instagram</h3><div class="admin-stat">' + m.with_instagram + '</div></div>' +
    '<div class="admin-card"><h3>With CID</h3><div class="admin-stat">' + m.with_cid + '</div></div>' +
    '<div class="admin-card"><h3>With Phone</h3><div class="admin-stat">' + m.with_phone + '</div></div>' +
    '<div class="admin-card"><h3>With Website</h3><div class="admin-stat">' + m.with_website + '</div></div>' +
    '<div class="admin-card"><h3>Last Build</h3><div class="admin-stat" style="font-size:0.7em">' + m.generated + '</div></div>' +
    '</div>' +
    '<h2>Invoice Status</h2><div id="invoice-table">Loading invoices...</div>';
  fetch('data/invoices.json').then(function(r){{ return r.json(); }}).then(function(invs) {{
    var html = '<table class="admin-table"><tr><th>Invoice</th><th>Business</th><th>Tier</th><th>Amount</th><th>Status</th><th>Paid</th></tr>';
    invs.forEach(function(i) {{
      var statusClass = i.status === 'paid' ? 'admin-paid' : (i.status === 'pending' ? 'admin-pending' : 'admin-cancelled');
      html += '<tr><td><a href="invoices/' + i.invoice_id + '.html">' + i.invoice_id + '</a></td><td>' + i.business_name + '</td><td>' + i.tier + '</td><td>$' + i.amount_usd + '</td><td class="' + statusClass + '">' + i.status + '</td><td>' + (i.paid_date || '-') + '</td></tr>';
    }});
    document.getElementById('invoice-table').innerHTML = html;
  }}).catch(function(){{ document.getElementById('invoice-table').innerHTML = 'No invoices yet.'; }});
}}).catch(function(){{ document.getElementById('admin-content').innerHTML = 'Error loading metrics.'; }});
</script>
</body>
</html>"""


def render_biz_dashboard_page(businesses):
    """Business owner dashboard — view your listing, analytics, premium status."""
    nav = nav_html("directory", depth=0)
    # Build biz data JSON safely outside f-string
    biz_data = json.dumps([{
        "name": b["name"], "slug": b["slug"], "category": b["category"],
        "area": b["area"], "rating": b.get("rating"),
        "phone": b["channels"]["phone"], "whatsapp": b["channels"]["whatsapp"],
        "instagram": b["channels"]["instagram"], "website": b["channels"]["website"],
    } for b in businesses], ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Business Dashboard — Paradisio</title>
<link rel="stylesheet" href="static/tokens.css">
<link rel="stylesheet" href="static/styles.css">
<script>
const LOCALE_DATA = {json.dumps(LOCALES, ensure_ascii=False)};
</script>
<script src="static/i18n.js"></script>
<script src="static/modes.js"></script>
</head>
<body>
{nav}
<div class="container">
<h1>Business Dashboard</h1>
<p class="subtitle">View and manage your business listing on Paradisio.</p>
<div class="biz-dashboard-search">
<input type="text" id="biz-search" placeholder="Find your business by name..." style="width:100%;padding:10px;font-size:1.1em;border:1px solid var(--sand-100);border-radius:6px;">
</div>
<div id="biz-dashboard-results">
  <p>Type your business name above to find your listing.</p>
</div>
</div>
<footer class="footer">
<p><a href="index.html">&larr; Back to directory</a></p>
</footer>
<script>
window.__bizData = {biz_data};
document.getElementById('biz-search').addEventListener('input', function(e) {{
  var q = e.target.value.toLowerCase();
  var results = document.getElementById('biz-dashboard-results');
  if (!q) {{ results.innerHTML = '<p>Type your business name above to find your listing.</p>'; return; }}
  var matches = window.__bizData.filter(function(b) {{ return b.name.toLowerCase().includes(q); }});
  if (!matches.length) {{ results.innerHTML = '<p>No matches found. Try a different name.</p>'; return; }}
  var html = '';
  matches.forEach(function(b) {{
    html += '<div class="result-card" style="padding:1em;margin-bottom:0.5em">' +
      '<div class="result-name"><a href="businesses/' + b.slug + '.html">' + b.name + '</a></div>' +
      '<div class="result-meta">' + (b.category||'') + ' · ' + (b.area||'') + (b.rating ? ' · â­ ' + b.rating : '') + '</div>' +
      '<div class="result-channels">' +
      (b.phone ? '<span>Phone: ' + b.phone + '</span> ' : '') +
      (b.whatsapp ? '<span>WA: ' + b.whatsapp + '</span> ' : '') +
      (b.instagram ? '<span>IG: @' + b.instagram + '</span>' : '') +
      '</div>' +
      '<div style="margin-top:0.5em"><a href="claim.html?biz=' + b.slug + '" class="claim-link">Claim or correct this page â†’</a></div>' +
      '</div>';
  }});
  results.innerHTML = html;
}});
</script>
</body>
</html>"""


def render_business_html(biz):
    nav = nav_html("directory", depth=1)
    name = html.escape(str(biz["name"]), quote=True)
    area = html.escape(str(biz["area"]), quote=True)
    description = html.escape(str(biz["description"] or "No description available."), quote=False)
    pc = biz["primary_contact"]
    report_url = html.escape((
        "https://github.com/skinnerboxentertainment/mekatelyu/issues/new?"
        f"template=business_correction.md&title={quote('Correction: ' + biz['name'])}"
    ), quote=True)
    sl = biz["secondary_links"]
    badges_html = " ".join(f'<span class="badge badge-{b.lower().replace(" ","-")}">{html.escape(b)}</span>' for b in biz["badges"])
    links_html = " ".join(
        f'<a href="{html.escape(l["url"], quote=True)}" class="secondary-link" target="_blank" rel="noopener">{html.escape(l["label"])}</a>'
        for l in sl
    )

    map_html = ""
    if biz["lat"] and biz["lng"]:
        lat = biz["lat"]
        lng = biz["lng"]
        cid = biz["channels"]["google_maps_cid"]
        map_url = f"https://www.google.com/maps?cid={cid}" if cid else f"https://www.google.com/maps?q={lat},{lng}"
        map_html = f"""<div class="biz-map">
<div id="map-{biz['slug']}" class="map-container" data-business-map data-lat="{lat}" data-lng="{lng}"></div>
<p class="map-note"><a href="{map_url}" target="_blank" rel="noopener">Open in Google Maps &rarr;</a></p>
</div>"""

    channel_type = pc["type"]
    share_row = f"""<div class="share-row">
<button class="share-trigger" data-share-trigger>Share this place &#183; <span class="share-icon">&#8600;</span></button>
</div>
<div class="share-sheet" data-share-sheet hidden>
<div class="share-sheet-inner">
<button class="share-option" data-share-copy>Copy link</button>
<a href="#" class="share-option" data-share-wa target="_blank" rel="noopener">Share via WhatsApp</a>
<button class="share-option" data-share-toggle-qr>Show QR code</button>
<button class="share-option share-close" data-share-close>Close</button>
</div>
<div class="share-qr" data-share-qr-panel hidden>
<img src="../qr/{biz['slug']}.png" alt="QR code for {name}" width="200" height="200" loading="lazy">
<a href="../qr/{biz['slug']}.png" class="qr-download-link" download>Download QR code</a>
</div>
</div>"""
    inline_cta = "" if channel_type == "None" else f"""<div class="biz-main hide-mobile">
<a href="{pc["url"]}" class="primary-cta" target="_blank" rel="noopener" data-plausible-event="ContactClick" data-plausible-channel="{channel_type}">{pc["label"]}</a>
</div>"""

    has_coords = bool(biz.get("lat") and biz.get("lng"))
    maps_url = ""
    if has_coords:
        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={biz['lat']},{biz['lng']}"
    elif biz["channels"].get("google_maps_cid"):
        maps_url = f"https://www.google.com/maps?cid={biz['channels']['google_maps_cid']}"

    call_ok = bool(biz['channels'].get('phone_normalized'))
    wa_ok = bool(biz['channels'].get('whatsapp'))
    show_call = call_ok and pc['type'] != 'Call'

    sticky_actions = ""
    if maps_url or show_call or True:
        parts = []
        if maps_url:
            parts.append(f'<a href="{maps_url}" class="sticky-directions" target="_blank" rel="noopener">Directions</a>')
        if show_call:
            parts.append(f'<a href="tel:{biz["channels"]["phone_normalized"]}" class="sticky-call" data-plausible-event="ContactClick" data-plausible-channel="Call">Call</a>')
        elif wa_ok:
            wa_url = biz["channels"]["whatsapp"]
            if wa_url.startswith("+"):
                wa_url = "https://wa.me/" + wa_url.lstrip("+")
            parts.append(f'<a href="{wa_url}" class="sticky-call" target="_blank" rel="noopener" data-plausible-event="ContactClick" data-plausible-channel="WhatsApp">WhatsApp</a>')
        parts.append('<button class="sticky-share" data-share-trigger>Share</button>')
        sticky_actions = f'<div class="sticky-bar">{"".join(parts)}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} — {area} — Whappin Puerto Viejo</title>
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https://*.tile.openstreetmap.org; connect-src 'self' https://*.tile.openstreetmap.org; object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests">
<link rel="canonical" href="https://www.whappin.com/businesses/{biz['slug']}.html">
<meta property="og:title" content="{name} — Whappin Puerto Viejo">
<meta property="og:description" content="{name} in {area}. View location and available contact options.">
<meta property="og:type" content="website">
<link rel="stylesheet" href="../static/tokens.css?v={TAXONOMY_VERSION}">
<link rel="stylesheet" href="../static/styles.css?v={TAXONOMY_VERSION}">
<link rel="stylesheet" href="../static/vendor/leaflet/leaflet.css">
<script src="../static/vendor/leaflet/leaflet.js"></script>
<meta name="description" content="{name} — {category_label(biz['category'])} in {area}, Puerto Viejo. View location and available contact options.">
</head>
<body>
{nav}
<main class="container">
<header class="header biz-header">
<a href="../index.html" class="back-link">&larr; Directory</a>
<h1>{name}</h1>
<div class="biz-meta">
<span class="biz-category">{category_label(biz["category"])}</span>
<span class="biz-area">{area}</span>
{status_html(biz["status"])}
</div>
<div class="badge-row">{badges_html}</div>
{rating_html(biz)}
{biz_addr(biz)}
{biz_hours(biz)}
{biz_semantic_facets(biz)}
{biz_amenities(biz)}
{biz_prices(biz)}
{biz_freshness(biz)}
</header>
{inline_cta}
<div class="biz-desc">
<p>{description}</p>
</div>
<div class="biz-content">
<div class="biz-links">{links_html}</div>
{map_html}
{share_row}
</div>
<footer class="footer">
<p><a href="{report_url}" target="_blank" rel="noopener">Suggest an edit</a></p>
</footer>
{sticky_actions}
</main>
<script src="../static/detail.js?v={TAXONOMY_VERSION}"></script>
</body>
</html>"""


CAT_LABELS = {
    "rooms-for-rent": "Rooms for Rent", "jobs": "Jobs", "gigs": "Gigs",
    "for-sale": "For Sale", "services": "Services", "events": "Events",
    "rideshare": "Rideshare", "lost-found": "Lost & Found",
}


def classifieds_url(ad):
    return f"../classifieds/{ad['slug']}.html"


def render_classifieds_index(ads):
    nav = nav_html("classifieds", depth=1)
    categories = {}
    for ad in ads:
        cat = ad["category"]
        categories.setdefault(cat, []).append(ad)
    cats_json = json.dumps({k: len(v) for k, v in categories.items()})
    labels_json = json.dumps(CAT_LABELS)
    ads_json = json.dumps(ads, ensure_ascii=False)

    cat_links = "".join(
        f'<a href="#cat-{cat}" class="cat-link">{CAT_LABELS.get(cat, cat)} ({len(items)})</a>'
        for cat, items in sorted(categories.items())
    )
    cat_sections = ""
    for cat, items in sorted(categories.items()):
        cards = "".join(
            f'<a href="{classifieds_url(ad)}" class="cl-card">'
            f'<div class="cl-title">{ad["title"]}</div>'
            f'<div class="cl-meta">{ad.get("area","")} · {ad.get("price","")}</div>'
            f'<div class="cl-summary">{ad["summary"][:120]}</div>'
            f'<div class="cl-date">{ad["posted_date"]}</div>'
            f"</a>"
            for ad in items
        )
        cat_sections += f'<h2 id="cat-{cat}" class="cl-cat-heading">{CAT_LABELS.get(cat, cat)} ({len(items)})</h2><div class="cl-grid">{cards}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Classifieds — Paradisio Puerto Viejo</title>
<link rel="stylesheet" href="../static/tokens.css">
<link rel="stylesheet" href="../static/styles.css">
<script>
const LOCALE_DATA = {json.dumps(LOCALES, ensure_ascii=False)};
</script>
<script src="../static/i18n.js"></script>
<script src="../static/modes.js"></script>
<script data-goatcounter="https://paradisio.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body>
{nav}
<div class="container">
<header class="header">
<h1>Classifieds</h1>
<p class="subtitle">Puerto Viejo community board · {len(ads)} active listings</p>
<div class="stats-bar">
<span class="stat"><strong>{len(ads)}</strong> listings</span>
<span class="stat"><strong>{len(categories)}</strong> categories</span>
</div>
</header>
<div class="controls">
<input type="text" id="cl-search" class="search-input" placeholder="Search classifieds..." autofocus>
<div class="cl-cat-nav">{cat_links}</div>
<div id="cl-count" class="stats-line"></div>
</div>
<div id="cl-results" class="cl-all">{cat_sections}</div>
<div class="post-ad-box">
<p><strong>Got something to sell, rent, or share?</strong></p>
<a href="mailto:paradisio@example.com?subject=Post%20classified&body=Category:%0ATitle:%0APrice:%0AArea:%0AContact:%0ADescription:" class="post-ad-btn">Post a free ad →</a>
</div>
<footer class="footer">
<p><a href="../index.html">Business Directory</a> · <a href="mailto:paradisio@example.com?subject=Post%20classified">Post an ad</a></p>
</footer>
</div>
<script>
const CLASSIFIEDS = {ads_json};
const CL_CATEGORIES = {cats_json};
const CL_LABELS = {labels_json};
</script>
<script src="../static/classifieds.js"></script>
</body>
</html>"""


def render_classified_listing(ad):
    nav = nav_html("classifieds", depth=1)
    cat_label = CAT_LABELS.get(ad["category"], ad["category"])
    contact_lines = []
    c = ad.get("contact", {})
    if c.get("whatsapp"):
        contact_lines.append(f'<a href="https://wa.me/{c["whatsapp"].lstrip("+")}" class="secondary-link" target="_blank">WhatsApp</a>')
    if c.get("phone"):
        contact_lines.append(f'<a href="tel:{c["phone"]}" class="secondary-link">Call {c["phone"]}</a>')
    if c.get("instagram"):
        contact_lines.append(f'<a href="https://instagram.com/{c["instagram"]}" class="secondary-link" target="_blank">@{c["instagram"]}</a>')
    if c.get("email"):
        contact_lines.append(f'<a href="mailto:{c["email"]}" class="secondary-link">Email</a>')

    tags = " ".join(f'<span class="channel-tag">{t}</span>' for t in ad.get("tags", []))
    contacts_html = " ".join(contact_lines) if contact_lines else '<span class="no-contact">Reply to this ad to inquire</span>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ad["title"]} — Paradisio Classifieds</title>
<link rel="stylesheet" href="../static/tokens.css">
<link rel="stylesheet" href="../static/styles.css">
<script>
const LOCALE_DATA = {json.dumps(LOCALES, ensure_ascii=False)};
</script>
<script src="../static/i18n.js"></script>
<script data-goatcounter="https://paradisio.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</head>
<body>
{nav}
<div class="container">
<a href="../classifieds/index.html" class="back-link">&larr; Classifieds</a>
<article class="cl-listing">
<h1>{ad["title"]}</h1>
<div class="biz-meta">
<span class="biz-category">{cat_label}</span>
<span class="biz-area">{ad.get("area", "")}</span>
</div>
<div class="cl-price">{ad.get("price", "") or "Free"}</div>
<div class="cl-date">Posted {ad["posted_date"]}</div>
<p class="cl-body">{ad["summary"]}</p>
{("<div class='cl-tags'>" + tags + "</div>") if ad.get("tags") else ""}
<div class="biz-claim">
<p><strong>Contact</strong></p>
<div class="biz-links">{contacts_html}</div>
</div>
</article>
<footer class="footer">
<p><a href="../classifieds/index.html">&larr; All classifieds</a> · <a href="../index.html">Business Directory</a></p>
</footer>
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
        "categories": {k: v for k, v in sorted(categories.items(), key=lambda x: -x[1])},
        "areas": {k: v for k, v in sorted(areas.items(), key=lambda x: -x[1])},
        "semantic_facets": {
            tag: sum(1 for b in businesses if tag in b["semantic_tags"] or tag in b["semantic_attributes"])
            for tag in sorted(TAG_LABELS)
            if any(tag in b["semantic_tags"] or tag in b["semantic_attributes"] for b in businesses)
        },
        "generated": os.environ.get("PARADISIO_BUILD_DATE") or datetime.now().strftime("%Y-%m-%d"),
    }

    print(f"Building Whappin Puerto Viejo — {len(businesses)} businesses")

    generate_profile_qr_codes(businesses)
    print(f"  qr/ — {len(businesses)} profile QR codes")

    biz_dir = OUTPUT_DIR / "businesses"
    for biz in businesses:
        html = render_business_html(biz)
        with open(biz_dir / f"{biz['slug']}.html", "w", encoding="utf-8") as f:
            f.write(html)
    print(f"  businesses/ — {len(businesses)} pages")

    index_html = render_index_html(businesses, metrics)
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  index.html — entry point")

    summaries = [public_business_summary(b) for b in businesses]
    directory_data = (
        "const BUSINESSES=" + json.dumps(summaries, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "const CATEGORIES=" + json.dumps(metrics["categories"], ensure_ascii=False, separators=(",", ":")) + ";\n"
        "const SEMANTIC_FACETS=" + json.dumps(metrics["semantic_facets"], ensure_ascii=False, separators=(",", ":")) + ";\n"
        "const SEMANTIC_LABELS=" + json.dumps(TAG_LABELS, ensure_ascii=False, separators=(",", ":")) + ";\n"
        "const AREAS=" + json.dumps(metrics["areas"], ensure_ascii=False, separators=(",", ":")) + ";\n"
    )
    (OUTPUT_DIR / "static" / "directory-data.js").write_text(directory_data, encoding="utf-8")

    static_src = STATIC_DIR / "app.js"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "app.js")
    static_src = STATIC_DIR / "detail.js"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "detail.js")
    static_src = STATIC_DIR / "tokens.css"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "tokens.css")
    static_src = STATIC_DIR / "styles.css"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "styles.css")
    vendor_src = STATIC_DIR / "vendor"
    if vendor_src.exists():
        shutil.copytree(vendor_src, OUTPUT_DIR / "static" / "vendor")
    print(f"  static/ — directory-data.js, tokens.css, app.js, detail.js, styles.css")

    urls = [PRODUCTION_BASE_URL + "/"] + [PRODUCTION_BASE_URL + f"/businesses/{b['slug']}.html" for b in businesses]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{url}</loc></url>\n" for url in urls)
    sitemap += "</urlset>\n"
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUTPUT_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {PRODUCTION_BASE_URL}/sitemap.xml\n", encoding="utf-8")
    print("  robots.txt + sitemap.xml")

    generate_deployment_wrapper()
    print("  release root — redirect, 404, robots, .nojekyll")

    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
