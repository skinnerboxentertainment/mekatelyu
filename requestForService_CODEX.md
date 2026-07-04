# Request for Service — Neighborhood Scanner for Puerto Viejo Business Discovery

**Target Agent**: CODEX
**Project**: Puerto Viejo Business Discovery — Phase 2 (Neighborhood Scanning)
**Date**: 2026-07-04

---

## Context

We have crawled Puerto Viejo Satellite (`puertoviejosatellite.com`) and extracted **450 businesses** within a 5 km radius of Puerto Viejo de Talamanca, Costa Rica. We have Instagram handles (300 verified via Playwright browser check), phone numbers, WhatsApp, Booking.com links, Facebook URLs, coordinates, and Google Maps CIDs. This is Phase 1.

**Phase 2 is the problem**: we don't know what we're *missing*. Around each of our 450 pins, Google Maps shows other businesses that we don't have in our dataset. We need a systematic way to discover them.

---

## The Dataset

We have `pv_within_5km_enriched_b.csv` — 450 records with these columns:

### Key columns

| Column | Coverage | Example |
|--------|----------|---------|
| `business_name` | 100% | `Black Bamboo` |
| `category` | 100% | `hotel`, `restaurant`, `shopping`, `services`, `tour_company`, `real_estate`, `hostel`, `vacation_rental` |
| `area` | 100% | `Puerto Viejo`, `Cocles`, `Playa Chiquita`, `Playa Negra`, `Punta Uva`, `Hone Creek` |
| `latitude` / `longitude` | 100% | `9.655909` / `-82.748043` |
| `distance_km` | 100% | `0.579` (distance from origin) |
| `instagram_handle` | 67% (300 verified) | `blackbamboo_bedandbreakfast` |
| `instagram_confidence` | 67% | `verified`, `confirmed`, `removed` |
| `phone` | 83% | `+506 8306 5489` |
| `normalized_phone` | 83% | `+50683065489` |
| `whatsapp` | 15% | `+50687903340` |
| `facebook_url` | 55% | `https://www.facebook.com/Black-Bamboo-892726704246164/` |
| `booking_url` | 38% | `https://www.booking.com/hotel/cr/black-bambino-b-amp-b.html` |
| `tripadvisor_url` | 13% | Affiliate links to TripAdvisor |
| `google_maps_cid` | 78% | `9649993079907777710` |
| `verified_date` | 100% | `2026-03-10` |
| `description_full` | 99% | Full-text listing description from PVS |
| `geofilter` | 100% | `pass` / `fail` |
| `coordinate_source` | 100% | `array` (from aLats/aLngs in category page JS) |

### Sample records

**Hotel with Instagram:**
```
business_name: Black Bamboo
category: hotel
area: Puerto Viejo
latitude: 9.655909, longitude: -82.748043
instagram_handle: blackbamboo_bedandbreakfast
instagram_confidence: verified
phone: +506 8306 5489
google_maps_cid: 9649993079907777710
verified_date: 2026-03-10
booking_url: https://www.booking.com/hotel/cr/black-bambino-b-amp-b.html?aid=1284953
```

**Restaurant with Instagram:**
```
business_name: Gigi O Restaurant
category: restaurant
area: Puerto Viejo
latitude: 9.657426, longitude: -82.751070
instagram_handle: wearegigio
instagram_confidence: verified
phone: +506 8676 7889
google_maps_cid: 4732141069441829785
```

**Service without Instagram:**
```
business_name: Amimodo Beach Rooms
category: hotel
area: Puerto Viejo
latitude: 9.659233, longitude: -82.750485
instagram_handle: (empty — removed by Playwright verification)
instagram_confidence: removed
phone: +506 2750 0257
booking_url: https://www.booking.com/hotel/cr/amimodobeachrooms.html?aid=1284953
```

### Sparse grid analysis

We divided the 5 km radius into 1 km × 1 km grid cells (~81 cells within range). Of these, **65 cells contain 3 or fewer businesses**. Many are in the ocean, jungle, or national park — but ~17 are in commercially plausible areas. These sparsely populated cells are where the Google Maps neighborhood scan would uncover missing businesses.

---

## The Problem

For each of the 450 coordinates, we need to know:

> *"What businesses does Google Maps show near this location that we don't have in our dataset?"*

Doing this manually requires opening 450 Maps URLs and reading the sidebar — impossible at scale. We need a browser-based tool that:

1. Opens Google Maps at each known coordinate
2. Extracts any visible business names from the sidebar/panel
3. Compares against our dataset
4. Reports businesses we're missing
5. Saves **screenshots** or DOM snapshots as evidence

---

## The Solution to Build

### Architecture

A Python script using **Playwright** (Chromium) that:

1. **Loads the dataset** from `pv_within_5km_enriched_b.csv`
2. **Builds a known-name index** — normalized names from our dataset for dedup
3. **For each coordinate with a Maps CID** (350 of 450):
   - Opens `https://www.google.com/maps?cid={cid}` in Playwright
   - Waits for the business sidebar to render
   - Extracts visible business names from the page
   - Cross-references against our known-name index
   - Takes a screenshot of the area showing surrounding businesses
   - Logs any businesses we don't have
4. **Produces a report**: businesses-to-investigate list with screenshots

### Technical Specifications

**Google Maps interaction:**

- Open at `https://www.google.com/maps?cid={cid}` for each business with a CID. This URL opens directly to the business's place card, which shows surrounding businesses in the sidebar.
- Handle **consent/cookie dialogs** — click "Accept all" or equivalent if present.
- Handle **login walls** — if Maps redirects to login, save the screenshot and move on. Don't try to authenticate.
- Set **browser locale to en-US** to get English UI for easier parsing.
- **Viewport**: 1400×800 to show sidebar + map.

**Sidebar extraction approach:**

The Google Maps sidebar shows nearby businesses in a scrollable list. If the page loads successfully, extract names using these strategies in order:

1. **Place card overlay**: The top-left place card (for the business itself) contains "People also search for" or "Nearby" sections with business links. Parse `a[role="link"]` elements with `aria-label` attributes.
2. **Scroll for nearby panel**: Scroll down in the sidebar to trigger "Nearby places" to load, then extract business names.
3. **Body text fallback**: If structured extraction fails, dump all visible text and use heuristic name extraction (3-80 char strings not matching UI labels).

**Deduplication:**

Our dataset uses `business_name` with a `- Playa X, Puerto Viejo, Limón...` suffix pattern. CODEX should:
- Normalize discovered names (strip location suffixes, lowercase, remove punctuation)
- Compare against a precomputed name index of all 450 known businesses
- Flag any name that doesn't match any known entry as a candidate

**Pacing and politeness:**

- **8-10 seconds** between each Maps page load
- Randomize user agent on each session
- Handle rate limiting: if Maps returns a CAPTCHA/challenge page, log it and move on
- Maximum 350 fetches (only businesses with CIDs), expected runtime ~45-55 minutes

**Resume capability:**

- Save progress to a JSON file every 20 businesses
- Track: which URLs have been scanned, which discoveries were made
- Restartable from any checkpoint

**Evidence collection:**

- For each scanned coordinate, save a **screenshot** (`scan_{index}_{name}.png`) showing the Maps view with sidebar
- This allows a human to verify discoveries manually

### Deliverables

1. **`discoveries.csv`** — businesses found in the neighborhood that aren't in our dataset, with:
   - `lat`, `lon` (center of the scan)
   - `source_business` (which known business led to this scan)
   - `discovered_name`, `discovered_type` (hotel/restaurant/etc. if detectable)
   - `maps_url` (Google Maps link for the area)
   - `screenshot_file` (path to evidence screenshot)
   - `confidence` (based on how clearly the name appeared)

2. **`scan_log.json`** — full scan log with:
   - Per-URL: success/failure, businesses found, screenshot path
   - Summary: total scanned, discoveries found, failures/bypasses

3. **`screenshots/` directory** — PNG files of each Maps view showing the surrounding area

4. **`scan_report.py`** — a summary script that prints stats from the log

---

## What NOT to do

- **Do not use Google Maps API** (no API key, no Places API, no billing)
- **Do not log in** to any Google account
- **Do not try to extract Instagram links** from Maps pages (we already know they're JS-loaded behind authentication)
- **Do not scrape reviews, photos, or detailed business data** — just the business names visible in the sidebar
- **Do not exceed 350 fetches total** — only businesses with CIDs, stop if rate-limited

---

## Existing Infrastructure CODEX Can Use

All files are at `C:\Users\oscar\AI WORKBENCH\Pura Vida Puerto Viejo\`.

| Resource | Path | Use it for... |
|----------|------|---------------|
| Full dataset | `pv_within_5km_enriched_b.csv` | Known-name index, coordinates, CIDs |
| Playwright | Already installed (`playwright` + Chromium) | Browser automation |
| Sparse cell analysis | `scan_targets.csv` (65 target cells) | Prioritization: scan sparse cells first |

---

## Success Criteria

The scan is complete when we can answer "yes" to all:

- [ ] At least 250 of 350 CID-based scans completed without errors
- [ ] At least one genuinely missing business discovered per zone
- [ ] Screenshots saved for human review of the top 20 most promising gaps
- [ ] The `discoveries.csv` file has clean, deduplicated entries ready for human verification
