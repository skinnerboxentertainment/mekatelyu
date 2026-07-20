# Paradisio — Puerto Viejo Business Board

**738 entity-resolved businesses across Puerto Viejo and Costa Rica's South Caribbean.**
A multi-source local business directory with validated contact routing, maps, ratings, amenities, and one profile QR code per establishment.

👉 **[Open Paradisio](https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app/)** — search, filter, map, and open available contact channels

---

## Dataset

**File:** `pv_master_unified.csv` — 738 records, 34 columns.

### Coverage

| Field | Records | Coverage |
|-------|---------|----------|
| Business name | 738 | 100% |
| Google Maps CID | 726 | 98% |
| Coordinates | 598 | 81% |
| Category | 738 | 100% |
| Area | 738 | 100% |
| Phone | 599 | 81% |
| Instagram | 444 | 60% |
| Facebook | 355 | 48% |
| Website | 182 | 25% |
| Booking.com | 170 | 23% |
| WhatsApp | 175 | 24% |
| Email | 72 | 10% |
| TripAdvisor | 64 | 9% |

### Categories

| Category | Count |
|----------|-------|
| Hotel | 198 |
| Restaurant | 192 |
| Vacation Rental | 150 |
| Services | 81 |
| Shopping | 54 |
| Tour Company | 27 |
| Hostel | 23 |
| Real Estate | 5 |
| Wellness | 5 |
| Transport | 3 |

### Areas

| Area | Count |
|------|-------|
| Puerto Viejo | 218 |
| Cocles | 94 |
| Cahuita | 94 |
| Playa Negra | 70 |
| Playa Chiquita | 55 |
| Punta Uva | 24 |
| Manzanillo | 24 |
| Hone Creek | 20 |
| Bribri | 7 |
| Sixaola | 7 |
| Gandoca | 6 |

### Column Definitions

| Column | Description |
|--------|-------------|
| `business_name` | Business name |
| `category` | Business category (hotel, hostel, vacation_rental, restaurant, shopping, services, tour_company, real_estate) |
| `area` | Town/beach area label |
| `latitude`, `longitude` | Coordinates |
| `distance_km` | Haversine distance from origin (9.655, -82.753) |
| `google_maps_cid` | Google Maps Place ID |
| `phone` | Raw phone number |
| `normalized_phone` | Cleaned phone number (+506 format) |
| `website` | Business website URL |
| `instagram_handle` | Instagram username |
| `instagram_url` | Full Instagram profile URL |
| `facebook_url` | Facebook page URL |
| `whatsapp` | WhatsApp number |
| `booking_url` | Booking.com listing URL |
| `tripadvisor_url` | TripAdvisor listing URL |
| `email` | Email address |
| `verified_date` | Date last verified |
| `operating_status` | `active`, `permanently_closed`, etc. |
| `coordinate_source` | Source of coordinates (`maps_stealth`, `pv_satellite`, `osm`) |

---

## Pipeline

```
1. PV Satellite Crawl
   └── httpx + BeautifulSoup → 593 listings from 8 category pages

2. Parse & Normalize
   └── Phone, Instagram, Facebook, Maps CID, verified date extraction

3. Geofilter (5 km radius)
   └── Coordinates from cached category pages
   └── Haversine distance → 450 businesses within range

4. OSM Cross-Reference
   └── Overpass API query → 303 matched, 148 PVS-only, 156 OSM-only

5. SQLite Cache Mining
   └── Preexisting crawl cache parsed → +139 records, +12 IG handles

6. Instagram Discovery & Verification
   └── Direct handle guessing → 450 candidates
   └── Playwright browser verification → 300 confirmed working

7. Stealth Maps Search (Google Maps, not Web Search)
   └── Playwright + real Chrome profile → 265 businesses resolved
   └── CIDs, coordinates, phones, websites extracted
   └── 25-45s randomized delays, 30/session → zero CAPTCHA

8. Website Crawl
   └── 191 websites visited → social links extracted
   └── 86 sites yielded Instagram, Facebook, WhatsApp, email links

9. Website Affiliate Cleanup
   └── 53 TripAdvisor affiliate URLs resolved to clean pages
   └── Zero affiliate wrappers remaining in dataset
```

### Data Sources

| Source | Records | Method |
|--------|---------|--------|
| PV Satellite | 450 | httpx crawl + parse |
| SQLite cache | 139 | SQLite dump + enrichment |
| OSM additions | 31 | Overpass API |
| Grid scan names | 134 | Screenshot + vision |
| **Current canonical total** | **738** | Entity-resolved launch dataset |

---

## Repository Structure

```
paradisio_app/              — Static web app generator (build.py, CSS, JS)
pv_master_unified.csv       — Master dataset (738 records, 34 cols)
pvscraper/                  — Reusable Python crawl + parse module
stealth_search.py           — Maps-direct CID/coords/phone resolver
website_crawl.py            — Business website social link extractor
codex_bridge.py             — Thin wrapper for Codex CLI delegation
CODEX_ENDPOINT/             — IPC hub for Codex task delegation
release/                    — Ignored, reproducible launch artifact
  paradisio_app/            — 738 business profiles and 738 QR codes
audit/launch-readiness/     — Internal audit, remediation, and verification records
```

### GitHub Pages

- **App:** `https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app/` ← main entry
- Each profile exposes its own downloadable QR code at `paradisio_app/qr/{slug}.png`.

### Build and verify

```powershell
python -m pip install -r requirements-launch.txt
python -m unittest discover -s tests -p "test_*.py" -v
python scripts/verify_source_data.py
python paradisio_app/build.py
python scripts/verify_release.py
```

The generated candidate is written to ignored `release/`. CI uploads that exact directory as a review artifact but does not deploy it.

### Key Scripts

| Script | Purpose |
|--------|---------|
| `stealth_search.py` | Launches real Chrome, searches Google Maps directly for each business, extracts CID + coords + phone + website. 25-45s delays, session-based, no CAPTCHA. |
| `website_crawl.py` | Visits all business websites, extracts Instagram/Facebook/WhatsApp/email/Booking links from HTML. |
| `pvscraper/` | Reusable module for PV Satellite crawling, parsing, normalization. |
| `crossref_osm.py` | OpenStreetMap Overpass API cross-reference. |
| `geofilter.py` | Haversine distance geofilter. |
| `ig_enrich.py` | Instagram handle guessing and verification. |

---

## v3.0 — Paradisio App

The Paradisio app (`paradisio_app/`) is a static, mobile-friendly web application that turns the dataset into a usable directory. Key features:

- **738 business profiles** with validated contact routing and one QR code per profile
- **Search, filters, paginated results** — category, area, contact channel, text search
- **Interactive cluster map** — toggle between list and map views
- **Star ratings, hours, amenities** — enriched from Google Maps CID crawl
- **Print-ready QR codes** for every business — download or print for stickers
- **Mobile-first responsive** — works on any device
- **Minimal public artifact** — no payment, administrative, invoice, claim, analytics, or classifieds surface in the reduced release

Built with Python, `qrcode`/Pillow, and vanilla HTML/CSS/JS. No application server or database is required.

---

## License

Data collected from publicly accessible web pages. OpenStreetMap data © OpenStreetMap contributors (ODbL). No API keys, no paid services.
