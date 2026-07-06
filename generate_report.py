"""
Generate comprehensive HTML report from the final enriched dataset.
"""

import csv
import json
import math
from collections import defaultdict, Counter
from datetime import datetime

INPUT_CSV = "pv_within_5km_verified.csv"
OUTPUT_HTML = "pv_report.html"


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def main():
    with open(INPUT_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    with_ig = [r for r in rows if r.get("instagram_handle")]
    without_ig = [r for r in rows if not r.get("instagram_handle")]
    ig_pct = round(len(with_ig) / total * 100, 1) if total else 0

    with_phone = sum(1 for r in rows if r.get("phone"))
    with_cid = sum(1 for r in rows if r.get("google_maps_cid"))
    with_website = sum(1 for r in rows if r.get("website"))
    with_fb = sum(1 for r in rows if r.get("facebook_url"))
    with_verified = sum(1 for r in rows if r.get("verified_date"))

    # Categories
    cats = sorted(set(r["category"] for r in rows))
    cat_counts = {c: sum(1 for r in rows if r["category"] == c) for c in cats}
    cat_ig = {c: sum(1 for r in rows if r["category"] == c and r.get("instagram_handle")) for c in cats}
    cat_ig_pct = {c: round(cat_ig[c] / cat_counts[c] * 100, 1) if cat_counts[c] else 0 for c in cats}

    # Areas
    areas = sorted(set(r["area"] for r in rows))
    area_counts = {a: sum(1 for r in rows if r["area"] == a) for a in areas}
    area_ig = {a: sum(1 for r in rows if r["area"] == a and r.get("instagram_handle")) for a in areas}

    # Cross-reference summary
    osm_both = []
    try:
        with open("pv_osm_both.csv", encoding="utf-8") as f:
            osm_both = list(csv.DictReader(f))
    except FileNotFoundError:
        pass

    osm_pvs_only = []
    try:
        with open("pv_osm_pvsonly.csv", encoding="utf-8") as f:
            osm_pvs_only = list(csv.DictReader(f))
    except FileNotFoundError:
        pass

    osm_only = []
    try:
        with open("pv_osm_osmonly.csv", encoding="utf-8") as f:
            osm_only = list(csv.DictReader(f))
    except FileNotFoundError:
        pass

    # Build GeoJSON features for the map
    features = []
    for r in rows:
        lat = r.get("latitude")
        lon = r.get("longitude")
        if not lat or not lon:
            continue
        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (ValueError, TypeError):
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon_f, lat_f]},
            "properties": {
                "name": r.get("business_name", "?")[:60],
                "category": r.get("category", ""),
                "area": r.get("area", ""),
                "instagram": r.get("instagram_handle") or "",
                "instagram_url": r.get("instagram_url") or "",
                "phone": r.get("normalized_phone") or r.get("phone") or "",
                "website": r.get("website") or "",
                "facebook": r.get("facebook_url") or "",
                "verified": r.get("verified_date") or "",
                "distance": r.get("distance_km", ""),
            },
        })

    geojson = {"type": "FeatureCollection", "features": features}

    # Color mapping by category
    cat_colors = {
        "hotel": "#e74c3c",
        "hostel": "#e67e22",
        "vacation_rental": "#f39c12",
        "restaurant": "#2ecc71",
        "shopping": "#3498db",
        "services": "#9b59b6",
        "tour_company": "#1abc9c",
        "real_estate": "#34495e",
    }

    # Build HTML
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Puerto Viejo Business Discovery - Report</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; color: #2c3e50; line-height: 1.6; }}
.header {{ background: linear-gradient(135deg, #2c3e50, #34495e); color: white; padding: 40px 20px; text-align: center; }}
.header h1 {{ font-size: 28px; margin-bottom: 8px; }}
.header p {{ font-size: 14px; opacity: 0.8; }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
.metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; margin-bottom: 30px; }}
.metric {{ background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.metric .value {{ font-size: 32px; font-weight: 700; color: #2c3e50; }}
.metric .label {{ font-size: 13px; color: #7f8c8d; margin-top: 4px; }}
.metric .sub {{ font-size: 11px; color: #95a5a6; }}
.card {{ background: white; border-radius: 10px; padding: 24px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.card h2 {{ font-size: 18px; margin-bottom: 16px; color: #2c3e50; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ecf0f1; }}
th {{ background: #f8f9fa; font-weight: 600; color: #7f8c8d; font-size: 12px; text-transform: uppercase; }}
tr:hover {{ background: #f8f9fa; }}
.bar-container {{ display: flex; align-items: center; gap: 8px; }}
.bar {{ height: 20px; border-radius: 4px; min-width: 4px; transition: width 0.3s; }}
.bar-label {{ font-size: 12px; color: #7f8c8d; white-space: nowrap; }}
.progress {{ height: 8px; background: #ecf0f1; border-radius: 4px; overflow: hidden; flex: 1; }}
.progress-fill {{ height: 100%; border-radius: 4px; transition: width 0.5s; }}
#map {{ height: 500px; border-radius: 8px; margin-bottom: 16px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 8px; font-size: 12px; }}
.legend-item {{ display: flex; align-items: center; gap: 4px; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
.ig-badge {{ background: #e74c3c; color: white; padding: 1px 6px; border-radius: 3px; font-size: 11px; }}
.ig-yes {{ background: #2ecc71; }}
.ig-no {{ background: #95a5a6; }}
.status {{ display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 11px; }}
.status-active {{ background: #d5f5e3; color: #27ae60; }}
.status-closed {{ background: #fadbd8; color: #e74c3c; }}
@media (max-width: 768px) {{ .metrics {{ grid-template-columns: repeat(2, 1fr); }} }}
</style>
</head>
<body>

<div class="header">
<h1>Puerto Viejo Business Discovery</h1>
<p>451 businesses within 5 km of Puerto Viejo de Talamanca, Costa Rica &mdash; Generated {now}</p>
</div>

<div class="container">

<div class="metrics">
<div class="metric"><div class="value">{total}</div><div class="label">Businesses</div><div class="sub">within 5 km</div></div>
<div class="metric"><div class="value">{len(with_ig)}</div><div class="label">Instagram</div><div class="sub">{ig_pct}% coverage</div></div>
<div class="metric"><div class="value">{len(cats)}</div><div class="label">Categories</div><div class="sub">{', '.join(c if c != 'vacation_rental' else 'vaca_rental' for c in cats[:4])} ...</div></div>
<div class="metric"><div class="value">{len(areas)}</div><div class="label">Areas</div><div class="sub">{', '.join(areas[:3])} ...</div></div>
<div class="metric"><div class="value">{with_phone}/{total}</div><div class="label">Phone</div><div class="sub">{round(with_phone/total*100,1)}% coverage</div></div>
<div class="metric"><div class="value">{with_cid}/{total}</div><div class="label">Google Maps</div><div class="sub">{round(with_cid/total*100,1)}% have CID</div></div>
</div>

<div class="card">
<h2>Interactive Map</h2>
<div id="map"></div>
<div class="legend">
"""

    for cat in cats:
        color = cat_colors.get(cat, "#95a5a6")
        label = cat.replace("_", " ").title()
        html += f'<div class="legend-item"><span class="legend-dot" style="background:{color}"></span>{label}</div>\n'

    html += f"""</div>
<p style="font-size:12px;color:#95a5a6;text-align:center;">{len(features)} businesses mapped. Click a marker for details.</p>
</div>

<div class="card">
<h2>Categories &mdash; Instagram Coverage</h2>
<table>
<tr><th>Category</th><th>Total</th><th>With Instagram</th><th>Coverage</th><th></th></tr>
"""

    for cat in cats:
        label = cat.replace("_", " ").title()
        count = cat_counts[cat]
        ig = cat_ig[cat]
        pct = cat_ig_pct[cat]
        bar_width = max(pct, 3)
        color = cat_colors.get(cat, "#3498db")
        html += f"""<tr>
<td><strong>{label}</strong></td>
<td>{count}</td>
<td>{ig}</td>
<td>{pct}%</td>
<td><div class="progress"><div class="progress-fill" style="width:{bar_width}%;background:{color}"></div></div></td>
</tr>\n"""

    html += f"""</table>
</div>

<div class="card">
<h2>Areas &mdash; Business Distribution</h2>
<table>
<tr><th>Area</th><th>Total</th><th>With Instagram</th><th>Distance from Origin</th></tr>
"""

    origin_lat, origin_lon = 9.6554, -82.7533
    for area in areas:
        count = area_counts[area]
        ig = area_ig[area]
        # Estimate distance from area center
        area_centers = {
            "Puerto Viejo": (9.6554, -82.7533),
            "Playa Negra": (9.660, -82.765),
            "Cocles": (9.642, -82.748),
            "Playa Chiquita": (9.632, -82.745),
            "Punta Uva": (9.622, -82.737),
            "Hone Creek": (9.675, -82.820),
        }
        ac = area_centers.get(area)
        dist_str = ""
        if ac:
            d = haversine_km(origin_lat, origin_lon, ac[0], ac[1])
            dist_str = f"{d:.1f} km"
        html += f"<tr><td><strong>{area}</strong></td><td>{count}</td><td>{ig}</td><td>{dist_str}</td></tr>\n"

    html += """</table>
</div>

<div class="card">
<h2>Data Quality</h2>
<table>
<tr><th>Field</th><th>Present</th><th>Missing</th><th>Coverage</th></tr>
"""

    quality_fields = [
        ("Business Name", total, 0),
        ("Phone", with_phone, total - with_phone),
        ("Google Maps CID", with_cid, total - with_cid),
        ("Website", with_website, total - with_website),
        ("Facebook", with_fb, total - with_fb),
        ("Instagram", len(with_ig), total - len(with_ig)),
        ("Verified Date", with_verified, total - with_verified),
    ]
    for label, present, missing in quality_fields:
        pct = round(present / total * 100, 1)
        bar_color = "#2ecc71" if pct > 80 else "#f39c12" if pct > 50 else "#e74c3c"
        html += f"""<tr>
<td>{label}</td><td>{present}</td><td>{missing}</td>
<td><div class="bar-container"><div class="progress" style="width:150px"><div class="progress-fill" style="width:{pct}%;background:{bar_color}"></div></div><span class="bar-label">{pct}%</span></div></td>
</tr>\n"""

    html += """</table>
</div>
"""

    # Cross-reference section
    if osm_both or osm_pvs_only or osm_only:
        html += """<div class="card">
<h2>OSM Cross-Reference</h2>
<table>
<tr><th>Source</th><th>Records</th></tr>
"""
        html += f"<tr><td>In both PVS + OSM</td><td>{len(osm_both)}</td></tr>\n"
        html += f"<tr><td>PVS only (not in OSM)</td><td>{len(osm_pvs_only)}</td></tr>\n"
        html += f"<tr><td>OSM only (not in PVS)</td><td>{len(osm_only)}</td></tr>\n"
        html += """</table>
</div>
"""

    # Sample records table
    html += """<div class="card">
<h2>Sample Records (first 30)</h2>
<div style="overflow-x:auto;">
<table>
<tr><th>Name</th><th>Category</th><th>Area</th><th>IG</th><th>Phone</th><th>Facebook</th><th>Distance</th></tr>
"""

    for r in rows[:30]:
        name = (r.get("business_name") or "?")[:50]
        cat = r.get("category", "")
        area = r.get("area", "")
        ig = r.get("instagram_handle", "") or ""
        ig_display = f'<span class="ig-badge ig-yes">Yes</span>' if ig else f'<span class="ig-badge ig-no">No</span>'
        phone = (r.get("normalized_phone") or r.get("phone") or "")[:18]
        fb = "Yes" if r.get("facebook_url") else ""
        dist = r.get("distance_km", "")
        html += f"<tr><td>{name}</td><td>{cat}</td><td>{area}</td><td>{ig_display}</td><td>{phone}</td><td>{fb}</td><td>{dist} km</td></tr>\n"

    html += """</table>
</div>
<p style="font-size:12px;color:#95a5a6;margin-top:8px;">Showing first 30 records. Full data in pv_within_5km_enriched2.csv</p>
</div>

</div>

<script>
// GeoJSON data embedded
var geojsonData = """
    geojson_str = json.dumps(geojson, ensure_ascii=False)
    html += geojson_str
    html += """;

// Category colors
var catColors = """
    html += json.dumps(cat_colors)
    html += """;

// Initialize map
var map = L.map('map').setView([9.6554, -82.7533], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
    maxZoom: 18,
}).addTo(map);

// Add 5 km radius circle
L.circle([9.6554, -82.7533], {
    radius: 5000,
    color: '#e74c3c',
    fillColor: '#e74c3c',
    fillOpacity: 0.05,
    weight: 2,
    dashArray: '5, 10',
}).addTo(map);

// Add origin marker
L.marker([9.6554, -82.7533], {
    icon: L.divIcon({ className: '', html: '<div style="background:#e74c3c;color:white;border-radius:50%;width:16px;height:16px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:bold;">★</div>', iconSize: [16, 16], iconAnchor: [8, 8] })
}).addTo(map).bindTooltip('Origin (5 km radius)', { direction: 'top' });

// Add business markers
L.geoJSON(geojsonData, {
    pointToLayer: function(feature, latlng) {
        var cat = feature.properties.category || 'unknown';
        var color = catColors[cat] || '#95a5a6';
        return L.circleMarker(latlng, {
            radius: 6,
            fillColor: color,
            color: '#fff',
            weight: 1.5,
            opacity: 1,
            fillOpacity: 0.8,
        });
    },
    onEachFeature: function(feature, layer) {
        var p = feature.properties;
        var igHtml = p.instagram ? '<a href="' + p.instagram_url + '" target="_blank">@' + p.instagram + '</a>' : '<span style="color:#95a5a6">Not found</span>';
        var phoneHtml = p.phone ? '&#9742; ' + p.phone : '';
        var fbHtml = p.facebook ? '<br>&#120143; <a href="' + p.facebook + '" target="_blank">Facebook</a>' : '';
        var distHtml = p.distance ? '<br>Distance: ' + p.distance + ' km' : '';
        var popup = '<strong>' + p.name + '</strong><br>'
            + p.category + ' &middot; ' + p.area + distHtml + '<br>'
            + 'Instagram: ' + igHtml + '<br>'
            + phoneHtml + fbHtml;
        layer.bindPopup(popup);
    }
}).addTo(map);
</script>

</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Report written to {OUTPUT_HTML} ({len(html):,} bytes)", flush=True)
    print(f"  {total} businesses mapped", flush=True)
    print(f"  {len(features)} features with coordinates", flush=True)


if __name__ == "__main__":
    main()
