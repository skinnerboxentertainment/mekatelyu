import csv
import json
import hashlib
import re
import os
import shutil
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "paradisio_app"
CSV_PATH = BASE_DIR.parent / "pv_master_unified.csv"
MAPS_ENRICH_PATH = OUTPUT_DIR / "data" / "maps_enrich.json"


def load_maps_enrich():
    path = MAPS_ENRICH_PATH
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    lookup = {}
    for r in records:
        if r["success"] and r["data"]:
            cid = r["cid"]
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
    raw = raw.strip()
    raw = re.sub(r"[^0-9+]", "", raw)
    if raw.startswith("+506") and len(raw) == 12:
        return raw
    if raw.startswith("506") and len(raw) == 11:
        return "+" + raw
    if raw.startswith("+") and len(raw) >= 10:
        return raw
    return raw.strip()


def has_whatsapp(row):
    wp = row.get("whatsapp", "").strip()
    if wp:
        return normalize_phone(wp)
    np = row.get("normalized_phone", "").strip()
    if np:
        return np
    p = row.get("phone", "").strip()
    if p:
        return normalize_phone(p)
    return ""


def contactability_score(row):
    score = 0
    if has_whatsapp(row): score += 40
    if row.get("phone", "").strip(): score += 30
    if row.get("instagram_handle", "").strip(): score += 15
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
    badges = []
    if has_whatsapp(row): badges.append("WhatsApp")
    ig = row.get("instagram_handle", "").strip()
    ig_conf = row.get("instagram_confidence", "").strip()
    if ig and ig_conf == "verified": badges.append("Instagram")
    if row.get("booking_url", "").strip(): badges.append("Booking")
    if row.get("google_maps_cid", "").strip(): badges.append("Map Verified")
    if row.get("website", "").strip(): badges.append("Has Website")
    if row.get("phone", "").strip() or row.get("normalized_phone", "").strip(): badges.append("Phone")
    cs = contactability_score(row)
    vs = visibility_score(row)
    if cs + vs > 140: badges.append("Fully Online")
    return badges


def get_intents(category):
    mapping = {
        "hotel": ["stay"],
        "vacation_rental": ["stay"],
        "hostel": ["stay"],
        "restaurant": ["eat"],
        "tour_company": ["tour"],
        "shopping": ["shop"],
        "services": ["service"],
    }
    return mapping.get(category.lower().strip(), ["other"])


def get_primary_contact(row):
    wp = has_whatsapp(row)
    if wp:
        message = WHATSAPP_TEMPLATE.format(name=row.get("business_name", ""))
        return {
            "type": "WhatsApp",
            "label": "Message on WhatsApp",
            "url": f"https://wa.me/{wp.lstrip('+')}?text={message}",
        }
    phone = row.get("phone", "").strip() or row.get("normalized_phone", "").strip()
    if phone:
        return {"type": "Call", "label": "Call", "url": f"tel:{phone}"}
    ig = row.get("instagram_handle", "").strip()
    if ig:
        return {"type": "Instagram", "label": "Instagram DM", "url": f"https://instagram.com/{ig}"}
    website = row.get("website", "").strip()
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
    links = []
    phone = row.get("phone", "").strip() or row.get("normalized_phone", "").strip()
    if phone:
        links.append({"label": "Call", "url": f"tel:{phone}"})
    ig = row.get("instagram_handle", "").strip()
    if ig:
        links.append({"label": "Instagram", "url": f"https://instagram.com/{ig}"})
    fb = row.get("facebook_url", "").strip()
    if fb:
        links.append({"label": "Facebook", "url": fb})
    website = row.get("website", "").strip()
    if website:
        links.append({"label": "Website", "url": website})
    booking = row.get("booking_url", "").strip()
    if booking:
        links.append({"label": "Booking.com", "url": booking})
    ta = row.get("tripadvisor_url", "").strip()
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


def maps_data(cid):
    global MAPS_CACHE
    if MAPS_CACHE is None:
        MAPS_CACHE = load_maps_enrich()
    return MAPS_CACHE.get(cid, {})


def build_business(row):
    name = clean_display_name(row.get("business_name", "").strip(), row.get("area", "").strip())
    area = row.get("area", "").strip()
    slug = slugify(row.get("business_name", "").strip(), area)
    cid = row.get("google_maps_cid", "").strip()
    enrich = maps_data(cid)
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
            "phone": row.get("phone", "").strip(),
            "phone_normalized": row.get("normalized_phone", "").strip(),
            "whatsapp": has_whatsapp(row),
            "instagram": row.get("instagram_handle", "").strip(),
            "instagram_verified": row.get("instagram_confidence", "").strip() == "verified",
            "facebook_url": row.get("facebook_url", "").strip(),
            "website": row.get("website", "").strip(),
            "booking_url": row.get("booking_url", "").strip(),
            "tripadvisor_url": row.get("tripadvisor_url", "").strip(),
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
        "intents": get_intents(row.get("category", "").strip()),
        "description": row.get("description_full", "").strip()[:500],
        "verified_date": row.get("verified_date", "").strip(),
        "claim": {"status": "unclaimed"},
        "rating": enrich.get("rating"),
        "maps_address": enrich.get("address"),
        "check_in": enrich.get("check_in"),
        "check_out": enrich.get("check_out"),
        "amenities": enrich.get("amenities", []),
        "prices": enrich.get("prices", [])[:3],
    }
    return business


def render_index_html(businesses, metrics):
    total = metrics["total"]
    with_wp = metrics["with_whatsapp"]
    with_ig = metrics["with_instagram"]
    with_phone = metrics["with_phone"]
    with_cid = metrics["with_cid"]
    date = metrics["generated"]

    categories_json = json.dumps(metrics["categories"])
    areas_json = json.dumps(metrics["areas"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Paradisio — Puerto Viejo Business Board</title>
<link rel="stylesheet" href="static/styles.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" crossorigin="">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" crossorigin="">
</head>
<body>
<div class="container">
<header class="header">
<h1>Paradisio</h1>
<p class="subtitle">Puerto Viejo Business Board &middot; {total} businesses</p>
<div class="stats-bar">
<span class="stat"><strong>{total}</strong> businesses</span>
<span class="stat"><strong>{with_wp}</strong> with WhatsApp</span>
<span class="stat"><strong>{with_ig}</strong> with Instagram</span>
<span class="stat"><strong>{with_phone}</strong> with Phone</span>
<span class="stat"><strong>{with_cid}</strong> on Google Maps</span>
</div>
<p class="updated hide-mobile">Generated {date}</p>
</header>
<div class="controls">
<input type="text" id="search" class="search-input" placeholder="Search businesses..." autofocus>
<div class="view-toggle">
<button id="view-list" class="view-btn active">List</button>
<button id="view-map" class="view-btn">Map</button>
</div>
<div class="filters">
<select id="category-filter" class="filter-select">
<option value="">All Categories</option>
</select>
<select id="area-filter" class="filter-select">
<option value="">All Areas</option>
</select>
<select id="channel-filter" class="filter-select">
<option value="">Any Contact</option>
<option value="whatsapp">Has WhatsApp</option>
<option value="instagram">Has Instagram</option>
<option value="phone">Has Phone</option>
<option value="website">Has Website</option>
<option value="booking">Has Booking.com</option>
<option value="maps">On Google Maps</option>
</select>
<select id="sort-filter" class="filter-select">
<option value="name">Sort: Name</option>
<option value="contactability">Sort: Best Contact</option>
<option value="completeness">Sort: Most Complete</option>
</select>
</div>
<div id="stats-line" class="stats-line"></div>
<div id="filter-chips" class="filter-chips"></div>
</div>
<div id="results" class="results">
<div class="loading">Loading directory...</div>
</div>
<div id="load-more" class="load-more"></div>
<div id="map-container" class="map-view"></div>
<footer class="footer">
<p>A Paradisio project &middot; Data from Puerto Viejo Satellite, OSM, Google Maps, Instagram &middot; <a href="#" id="claim-link">Claim your business</a></p>
</footer>
</div>
<script>
const BUSINESSES = {json.dumps(businesses, ensure_ascii=False)};
const CATEGORIES = {categories_json};
const AREAS = {areas_json};
</script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js" crossorigin=""></script>
<script src="static/app.js"></script>
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
    a = biz.get("maps_address")
    return f'<div class="biz-addr">{a}</div>' if a else ""


def clean_time(t):
    return t.replace("?", "").replace("\u202f", " ") if t else ""

def biz_hours(biz):
    ci = clean_time(biz.get("check_in"))
    co = clean_time(biz.get("check_out"))
    if ci and co:
        return f'<div class="biz-hours">Check-in {ci} / Check-out {co}</div>'
    if ci:
        return f'<div class="biz-hours">Check-in {ci}</div>'
    if co:
        return f'<div class="biz-hours">Check-out {co}</div>'
    return ""


def biz_amenities(biz):
    am = biz.get("amenities", [])
    if not am:
        return ""
    # Filter out Maps UI noise and deduplicate
    noise = {"restaurantes", "hoteles", "bares", "cafes", "farmacias", "estacionamientos",
             "cosas que hacer", "guardado", "recientes", "transporte publico", "cajeros automaticos"}
    filtered = []
    seen = set()
    for a in am:
        key = a.lower().strip()
        if key in noise or key in seen:
            continue
        seen.add(key)
        filtered.append(a)
    if not filtered:
        return ""
    chips = " ".join(f'<span class="amenity-chip">{a}</span>' for a in filtered[:6])
    return f'<div class="amenities">{chips}</div>'


def render_business_html(biz):
    pc = biz["primary_contact"]
    sl = biz["secondary_links"]
    badges_html = " ".join(f'<span class="badge badge-{b.lower().replace(" ","-")}">{b}</span>' for b in biz["badges"])
    links_html = " ".join(f'<a href="{l["url"]}" class="secondary-link" target="_blank" rel="noopener">{l["label"]}</a>' for l in sl)
    scores = biz["scores"]

    map_html = ""
    if biz["lat"] and biz["lng"]:
        lat = biz["lat"]
        lng = biz["lng"]
        cid = biz["channels"]["google_maps_cid"]
        map_url = f"https://www.google.com/maps?cid={cid}" if cid else f"https://www.google.com/maps?q={lat},{lng}"
        map_html = f"""<div class="biz-map">
<div id="map-{biz['slug']}" class="map-container"></div>
<p class="map-note"><a href="{map_url}" target="_blank" rel="noopener">Open in Google Maps &rarr;</a></p>
</div>
<script>
document.addEventListener('DOMContentLoaded', function() {{
    var map = L.map('map-{biz['slug']}', {{ zoomControl: false, attributionControl: false }}).setView([{lat}, {lng}], 15);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
    L.marker([{lat}, {lng}]).addTo(map);
}});
</script>"""

    slug = biz["slug"]
    qr_img = f"../qr/{slug}.png" if Path(OUTPUT_DIR / "qr" / f"{slug}.png").exists() else None

    qr_section = ""
    if qr_img:
        qr_section = f"""<div class="biz-qr">
<div class="qr-preview">
<img src="{qr_img}" alt="QR code for {biz['name']}" width="120" height="120" loading="lazy">
<div class="qr-preview-text">
<strong>QR code ready</strong>
<p>Print this QR sticker and put it on your door. Every scan opens your page and WhatsApp.</p>
<a href="../qr/{slug}.png" class="qr-download-link" download>Download QR PNG &rarr;</a>
</div>
</div>
</div>"""

    inline_cta = f"""<div class="biz-main hide-mobile">
<a href="{pc["url"]}" class="primary-cta" target="_blank" rel="noopener">{pc["label"]}</a>
</div>"""

    sticky_cta = f"""<div class="sticky-bar">
<a href="{pc["url"]}" class="primary-cta" target="_blank" rel="noopener">{pc["label"]}</a>
{'<a href="tel:' + biz['channels']['phone_normalized'] + '" class="secondary-btn">Call</a>' if biz['channels']['phone_normalized'] and pc['type'] != 'Call' else ''}
{'<a href="https://instagram.com/' + biz['channels']['instagram'] + '" class="secondary-btn">IG</a>' if biz['channels']['instagram'] and pc['type'] != 'Instagram' else ''}
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{biz["name"]} — {biz["area"]} — Paradisio</title>
<link rel="stylesheet" href="../static/styles.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<meta name="description" content="{biz["name"]} — {biz["category"]} in {biz["area"]}, Puerto Viejo. Contact via WhatsApp, phone, or Instagram.">
</head>
<body>
<div class="container">
<header class="header biz-header">
<a href="../index.html" class="back-link">&larr; Back to directory</a>
<h1>{biz["name"]}</h1>
<div class="biz-meta">
<span class="biz-category">{biz["category"].title()}</span>
<span class="biz-area">{biz["area"]}</span>
<span class="biz-status status-{biz["status"]}">{biz["status"].title()}</span>
</div>
<div class="badge-row">{badges_html}</div>
{rating_html(biz)}
{biz_addr(biz)}
{biz_hours(biz)}
{biz_amenities(biz)}
</header>
{inline_cta}
<div class="biz-content">
<div class="biz-links">{links_html}</div>
{map_html}
{qr_section}
<div class="biz-scores">
<div class="score-bar"><span class="score-label">Contactability</span><div class="bar"><div class="bar-fill" style="width:{scores["contactability"]}%"></div></div><span class="score-num">{scores["contactability"]}</span></div>
<div class="score-bar"><span class="score-label">Visibility</span><div class="bar"><div class="bar-fill" style="width:{scores["visibility"]}%"></div></div><span class="score-num">{scores["visibility"]}</span></div>
<div class="score-bar"><span class="score-label">Completeness</span><div class="bar"><div class="bar-fill" style="width:{scores["completeness"]}%"></div></div><span class="score-num">{scores["completeness"]}</span></div>
</div>
<div class="biz-desc">
<p>{biz["description"] or "No description available."}</p>
</div>
<div class="biz-claim">
<p><strong>Is this your business?</strong></p>
<a href="mailto:paradisio@example.com?subject=Claim%20{biz['slug']}&body=I%20own%20{biz['name']}%20in%20{biz['area']}." class="claim-link">Claim or correct this page &rarr;</a>
</div>
<footer class="footer">
<p><a href="../index.html">&larr; Back to directory</a></p>
</footer>
</div>
{sticky_cta}
</body>
</html>"""


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "businesses").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "data").mkdir(parents=True, exist_ok=True)
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
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    print(f"Building Paradisio Board — {len(businesses)} businesses")

    data_dir = OUTPUT_DIR / "data"
    with open(data_dir / "businesses.json", "w", encoding="utf-8") as f:
        json.dump(businesses, f, ensure_ascii=False, indent=2)
    print(f"  businesses.json — {len(businesses)} records")

    with open(data_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"  metrics.json — {len(metrics)} fields")

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

    static_src = STATIC_DIR / "app.js"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "app.js")
    static_src = STATIC_DIR / "styles.css"
    if static_src.exists():
        shutil.copy2(static_src, OUTPUT_DIR / "static" / "styles.css")
    print(f"  static/ — app.js, styles.css")

    print(f"\nDone. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
