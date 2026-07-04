# Puerto Viejo Business Discovery — v1.0

**450 businesses within 5 km of Puerto Viejo de Talamanca, Costa Rica.**  
A verified, cross-referenced local business directory with Instagram handles, phone numbers, WhatsApp, Booking.com links, Facebook pages, and geographic coordinates.

---

## Dataset

**File:** `pv_within_5km_enriched_b.csv` — 450 records, 32 columns.

### Coverage

| Field | Records | Coverage |
|-------|---------|----------|
| Business name | 450 | 100% |
| Category | 450 | 100% |
| Area | 450 | 100% |
| Coordinates | 450 | 100% |
| Distance from origin | 450 | 100% |
| Verified date | 450 | 100% |
| Google Maps CID | 350 | 78% |
| Phone | 375 | 83% |
| Instagram (verified working) | 300 | 67% |
| Facebook | 246 | 55% |
| Booking.com | 171 | 38% |
| TripAdvisor | 57 | 13% |
| WhatsApp | 68 | 15% |
| Operating status | 450 | 100% |

### Categories

| Category | Count |
|----------|-------|
| Hotel | 96 |
| Vacation Rental | 109 |
| Restaurant | 94 |
| Services | 63 |
| Shopping | 44 |
| Tour Company | 23 |
| Hostel | 17 |
| Real Estate | 5 |

### Areas

| Area | Count |
|------|-------|
| Puerto Viejo | 199 |
| Cahuita | 95 |
| Cocles | 84 |
| Playa Negra | 69 |
| Playa Chiquita | 54 |
| Manzanillo | 25 |
| Punta Uva | 24 |
| Hone Creek | 20 |
| Sixaola | 8 |
| Bribri | 7 |
| Gandoca | 7 |

*Note: The 5 km geofilter includes Puerto Viejo, Playa Negra, Cocles, Playa Chiquita, Punta Uva, and Hone Creek. The other areas are in the dataset but filtered out of the primary set.*

### Column Definitions

| Column | Description |
|--------|-------------|
| `business_name` | Business name from PV Satellite listing |
| `category` | Business category (hotel, hostel, vacation_rental, restaurant, shopping, services, tour_company, real_estate) |
| `area` | Town/beach area label |
| `latitude`, `longitude` | Coordinates from PVS category page aLats/aLngs arrays |
| `distance_km` | Haversine distance from origin (9.6554, -82.7533) |
| `geofilter` | `pass` (within 5 km) or `fail` (outside) |
| `google_maps_cid` | Google Maps Place ID for direct Maps link |
| `phone` | Raw phone number as listed on PVS |
| `normalized_phone` | Cleaned phone number (+506XXXXXXXX format) |
| `instagram_handle` | Instagram username (verified working via Playwright browser check) |
| `instagram_confidence` | `verified` (browser-confirmed), `confirmed` (from PVS), `removed` (broken handle) |
| `instagram_url` | Full Instagram profile URL |
| `whatsapp` | WhatsApp number extracted from PVS listing |
| `facebook_url` | Facebook page URL |
| `booking_url` | Booking.com affiliate link |
| `tripadvisor_url` | TripAdvisor affiliate link |
| `website` | Business website (mostly TripAdvisor affiliate links; ~15 are real business domains) |
| `verified_date` | Date PVS last verified this listing (YYYY-MM-DD) |
| `operating_status` | `active`, `closed`, `temporarily_closed`, `needs_verification` |
| `ig_verified` | `true` / `false` — result of Playwright browser verification |
| `description_full` | Full listing description from PVS |
| `url` | Source URL on PV Satellite |

---

## Pipeline

The data was built through this process:

```
1. PV Satellite Crawl
   └── httpx + BeautifulSoup → 593 listings from all 8 category pages
   
2. Parse & Normalize
   └── Extract phone, Instagram, Facebook, Maps CID, verified date
   
3. Geofilter (5 km radius)
   └── Coordinates from aLats/aLngs arrays in cached category pages
   └── Haversine distance → 451 businesses within range
   └── Punta Uva and Hone Creek included by exception
   
4. OSM Cross-Reference
   └── Overpass API query → 303 matched, 148 PVS-only, 156 OSM-only
   
5. Instagram Discovery
   └── Direct handle guessing from business names → 450 candidates
   └── Playwright browser verification → 300 confirmed working, 150 removed
   
6. Enrichment
   └── WhatsApp, email, social links from cached HTML
   └── Booking.com and TripAdvisor links from cached HTML
```

### What was attempted and hit walls

| Method | Result | Why |
|--------|--------|-----|
| DuckDuckGo search for IG | Rate-limited | ~3 queries before 202 responses |
| Google Custom Search | Not attempted | Requires API key |
| Google Maps CID scraping | No social data | IG links JS-loaded behind auth |
| Facebook scraping | Not attempted | Requires login |
| Website crawling | ~15 real sites | Most "websites" are affiliate links |

---

## Repository Structure

```
pv_within_5km_enriched_b.csv   — Master dataset (450 records)
geofilter.py                   — Coordinate parsing + Haversine geofilter
pvscraper/                     — Reusable Python crawl + parse module
  __init__.py
  schema.py                    — SQLite schema, BusinessListing dataclass
  fetcher.py                   — httpx-based polite fetcher with caching
  enumerator.py                — Category page URL discovery
  parser.py                    — HTML extraction from PVS listing pages
  normalizer.py                — Phone/Instagram/URL cleaning
  pipeline.py                  — Orchestrate crawl → parse → normalize → store
  auditor.py                   — Coverage stats and quality report
docs/                          — GitHub Pages site
  index.html                   — Landing page
  directory.html               — Interactive business directory with map
  report.html                  — Analytical report with charts + map
  gapmap.html                  — Grid-based gap scanner for visual analysis
  businesses.json              — All 450 records as JSON for directory
  businesses.geojson           — GeoJSON for Google My Maps / QGIS
  dataset.csv                  — Latest dataset copy
requestForService_CODEX.md     — Brief for v2 grid scanner development
```

### GitHub Pages

- **Directory:** `https://skinnerboxentertainment.github.io/puerto-viejo-business-discovery/directory.html`
- **Report:** `https://skinnerboxentertainment.github.io/puerto-viejo-business-discovery/report.html`
- **Gap Map:** `https://skinnerboxentertainment.github.io/puerto-viejo-business-discovery/gapmap.html`
- **GeoJSON:** `https://skinnerboxentertainment.github.io/puerto-viejo-business-discovery/businesses.geojson`

---

## Using the pvscraper Module

```python
from pvscraper import ListingStore, Fetcher, Enumerator, ListingParser, Normalizer, Pipeline

store = ListingStore("pvscraper.db")
fetcher = Fetcher(store, min_delay=2.5)
enumerator = Enumerator(fetcher, store)
parser = ListingParser()
normalizer = Normalizer()

pipeline = Pipeline(store, fetcher, enumerator, parser, normalizer)
results = pipeline.run({"hotel": "/en/hotels/", "restaurant": "/en/restaurants/"})
```

Or use individual components for custom workflows. The `pvscraper/` module is self-contained with no external dependencies beyond `httpx`, `beautifulsoup4`, and `sqlite3`.

---

## v1.0 Release

This is the initial release. The dataset is accurate as of the PVS crawl date (2026-07-03). Instagram handles were browser-verified on 2026-07-04.

### v2.0 Planned

A grid-based Google Maps neighborhood scanner to discover businesses missing from the PVS dataset, using Playwright for structured search queries by zone. See `requestForService_CODEX.md` for the full brief.

---

## License

Data collected from publicly accessible web pages. OpenStreetMap data © OpenStreetMap contributors (ODbL). Instagram handles verified against publicly visible profile pages. No API keys, no login credentials, no paid services were used.
