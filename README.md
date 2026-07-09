# Paradisio — Puerto Viejo Business Board

**750 businesses within 5 km of Puerto Viejo de Talamanca, Costa Rica.**  
A verified, multi-source local business directory with Instagram handles, phone numbers, WhatsApp, Booking.com links, Facebook pages, Google Maps CIDs, coordinates, star ratings, amenities, and classifieds.

👉 **[Open Paradisio App](https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app/)** — search, filter, map, WhatsApp contact, classifieds board

<p align="center">
  <img src="docs/paradisio_app/qr/paradisio-app.png" width="160" height="160" alt="QR Code — scan to open Paradisio">
</p>
📋 **[Interactive Directory](https://skinnerboxentertainment.github.io/mekatelyu/directory.html)** — classic map + list view
🗺️ **[Gap Scanner Map](https://skinnerboxentertainment.github.io/mekatelyu/gapmap.html)** — visual grid analysis of coverage
📊 **[Full Report](https://skinnerboxentertainment.github.io/mekatelyu/report.html)** — aggregate stats, charts, enrichment breakdown

---

## Dataset

**File:** `pv_master_unified.csv` — 750 records, 34 columns.

### Coverage

| Field | Records | Coverage |
|-------|---------|----------|
| Business name | 750 | 100% |
| Google Maps CID | 699 | 93% |
| Coordinates | 606 | 81% |
| Category | 619 | 83% |
| Area | 619 | 83% |
| Phone | 611 | 81% |
| Instagram | 385 | 51% |
| Facebook | 361 | 48% |
| Website | 191 | 25% |
| Booking.com | 171 | 23% |
| WhatsApp | 106 | 14% |
| Email | 75 | 10% |
| TripAdvisor | 68 | 9% |

### Categories

| Category | Count |
|----------|-------|
| Hotel | 169 |
| Vacation Rental | 145 |
| Restaurant | 118 |
| Services | 77 |
| Shopping | 52 |
| Tour Company | 31 |
| Hostel | 22 |
| Real Estate | 5 |

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
| **Total unique** | **750** | Merge + dedup |

---

## Repository Structure

```
paradisio_app/              — Static web app generator (build.py, CSS, JS)
pv_master_unified.csv       — Master dataset (750 records, 34 cols)
pvscraper/                  — Reusable Python crawl + parse module
stealth_search.py           — Maps-direct CID/coords/phone resolver
website_crawl.py            — Business website social link extractor
codex_bridge.py             — Thin wrapper for Codex CLI delegation
CODEX_ENDPOINT/             — IPC hub for Codex task delegation
docs/                       — GitHub Pages site
  paradisio_app/            — Generated static app (750 business pages + classifieds)
  index.html                — Landing page (redirects to app)
  directory.html            — Classic interactive directory
  report.html               — Analytical report
  gapmap.html               — Grid-based gap scanner
  audit.html                — Data audit dashboard
```

### GitHub Pages

- **App:** `https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app/` ← main entry
- **Directory:** `https://skinnerboxentertainment.github.io/mekatelyu/directory.html`
- **Report:** `https://skinnerboxentertainment.github.io/mekatelyu/report.html`
- **Gap Map:** `https://skinnerboxentertainment.github.io/mekatelyu/gapmap.html`
- **Audit:** `https://skinnerboxentertainment.github.io/mekatelyu/audit.html`
- **QR Codes (print):** `https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app/qr/index.html`

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

- **750 business pages** with contact routing (WhatsApp > phone > Instagram > website > map)
- **Search, filters, paginated results** — category, area, contact channel, text search
- **Interactive cluster map** — toggle between list and map views
- **Star ratings, hours, amenities** — enriched from Google Maps CID crawl
- **Print-ready QR codes** for every business — download or print for stickers
- **Classifieds board** — rooms for rent, jobs, gigs, for sale, services, events, rideshare
- **Mobile-first responsive** — works on any device
- **GoatCounter analytics** — pageview tracking

Built with pure Python (stdlib) and vanilla HTML/CSS/JS. No frameworks, no database, no server. Runs entirely on GitHub Pages.

---

## License

Data collected from publicly accessible web pages. OpenStreetMap data © OpenStreetMap contributors (ODbL). No API keys, no paid services.
