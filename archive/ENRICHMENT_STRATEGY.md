# Comprehensive Data Enrichment Strategy

**Goal:** Turn our 615-candidate business directory into the richest possible
snapshot of Puerto Viejo's commercial landscape. Every record with phone,
website, Instagram, Facebook, Booking.com, Airbnb, WhatsApp, email, CID,
coordinates, and operating status.

**Constraint:** Zero Google Search risk unless specifically stated. We have
other paths.

---

## Phase 0 — Low-Hanging Fruit (zero risk, <2 hours)

### 0.1 Mine the PVS cache (`pvscraper_full.db`)
The raw SQLite from the original crawl. May contain phone numbers, Instagram
handles, website URLs, and other fields we never extracted into the CSV.

**Assets:** Any missing phone, IG, website, Facebook for the 450 PVS records.
**Risk:** None — local file.

### 0.2 Extract OSM contact tags
The `pv_osm_osmonly.csv` has a `tags` column with JSON blobs containing
`contact:facebook`, `contact:instagram`, `contact:phone`, `email`, `website`.
We only extracted a subset during the initial OSM pass — there may be more.

**Assets:** Facebook URLs, email addresses, additional phone numbers.
**Risk:** None — local file.

### 0.3 Crawl the 81 real websites
81 businesses have real websites (not TripAdvisor/Booking affiliates). Each
site is a potential goldmine: Instagram links, Facebook pages, email
addresses, WhatsApp numbers, Booking.com affiliate codes, Airbnb listings.

**Assets:** IG, FB, email, WhatsApp, booking links.
**Risk:** Near-zero — we're a polite HTTP visitor to business sites.

### 0.4 Hex CID recovery on all 350 CIDs
For every existing CID we already have, construct `https://www.google.com/maps?cid=XXXX`
and do a lightweight HEAD request — the redirect will resolve to a Maps URL
containing `!1s0xHEX1:0xHEX2!`. The hex pair may encode phone, website, or
other data embedded in the Maps listing.

**Assets:** Potentially richer CID metadata.
**Risk:** Minimal — single redirect per CID, no search queries.

### 0.5 Cross-reference with Booking.com search
For hotels and vacation rentals (206 records), search Booking.com by name + area.
Many will have Booking.com listings that include phone, website, reviews, pricing.

**Assets:** Booking.com URLs, review counts, pricing ranges.
**Risk:** Low — one polite query per business on Booking.com.

---

## Phase 1 — Instagram Expansion (zero Google risk)

### 1.1 Handle guessing for the ~300 without IG
Generate candidate handles from business names:
- `blackbamboo` → try `blackbamboo`, `blackbamboo_cr`, `blackbamboocr`, `blackbamboo_pv`
- Use common patterns (underscores, dots, abbreviations)
- Verify against Instagram's public profile page (returns 200 vs 404)

**Assets:** ~50-100 more working IG handles from the remaining 300.
**Risk:** Low — 1 HTTP request per guess, 3-5 guesses per business.
**Tool:** Playwright or httpx with polite delays.

### 1.2 Instagram profile scraping
For each verified IG handle, scrape the profile page for:
- Bio text (often contains website, email, WhatsApp)
- Profile image
- Follower count (indicates activity level)
- Link in bio (often contains website or Booking/Airbnb)

**Assets:** Website links, emails, WhatsApp from bios. ~300 profiles.
**Risk:** Low-medium — Instagram blocks aggressive scraping but is more
lenient than Google. 2-3s between requests.

---

## Phase 2 — Social Platform Discovery (low risk)

### 2.1 Facebook page search by phone number
For the ~250 with phone but no Facebook URL, search the phone number on
Facebook. Many Facebook business pages have phone numbers indexed.

**Assets:** Facebook URLs for businesses we're missing them.
**Risk:** Low — Facebook is more permissive than Google for direct lookups.

### 2.2 WhatsApp number verification
For all records, check if phone numbers have WhatsApp by attempting a
`wa.me/+506XXXXXXXX` link. WhatsApp returns a distinct page for active accounts.

**Assets:** Confirmed WhatsApp links (~68 existing → potentially 300+).
**Risk:** Near-zero — single HTTP request per phone.

### 2.3 Twitter/X discovery
Search for business names on Twitter. Many hospitality businesses in Costa Rica
have Twitter accounts even if they don't heavily use them.

**Assets:** Twitter URLs.
**Risk:** Low — polite search queries.

### 2.4 TikTok discovery
Search for business names on TikTok. Growing platform for Costa Rican tourism.

**Assets:** TikTok URLs.
**Risk:** Low.

---

## Phase 3 — Third-Party Platform Enrichment (low-medium risk)

### 3.1 Booking.com bulk lookup
For all 206 hotels + vacation rentals:
- Search Booking.com by name + Puerto Viejo
- Extract: Booking.com URL, review score, review count, price range, property type
- Can be automated with Playwright at low pace

**Assets:** ~150 more Booking URLs, review data for competitive analysis.
**Risk:** Low-medium — Booking.com has reasonable rate limits.

### 3.2 Airbnb search
Same approach for Airbnb. Many vacation rentals and some hotels list on Airbnb.
Search by name + area, extract listing URL, review count, price.

**Assets:** Airbnb URLs, pricing intelligence.
**Risk:** Low-medium.

### 3.3 TripAdvisor search
Similar to Booking.com for the ~393 without TripAdvisor URLs.
Search TA by name + Puerto Viejo.

**Assets:** TripAdvisor URLs, review data.
**Risk:** Low.

### 3.4 Expedia / Hotels.com / Agoda
Search the major OTA (online travel agency) platforms for hotel and
vacation rental listings.

**Assets:** Cross-platform listing data, pricing arbitrage intel.
**Risk:** Low.

### 3.5 Couchsurfing / Hostelworld
For hostels (20 records) and budget accommodations.
Hostelworld has detailed listings with phone, website, reviews.

**Assets:** Hostelworld URLs, alternative booking channels.
**Risk:** Low.

---

## Phase 4 — Google Maps Enrichment (the main event)

### 4.1 Slow stealth search for the 134 grid names
The remaining 134 names with no coordinates or CIDs. Each search takes
45-120s, with micro-sessions of 8-12, 20-40 per day. Real Chrome,
persistent profile, human-like delays.

This resolves names → CIDs → coordinates → phone → website.

**Assets:** CIDs, coordinates, phone, website for all 134.
**Risk:** Moderate — Google CAPTCHA possible, but pacing mitigates.
**Timeline:** 3-8 days at conservative pacing.

### 4.2 Slow search for missing CIDs (100 PVS + 31 OSM)
Same approach for the 131 records with coordinates but no CID.
These are faster because we already know the area — the search is targeted.

**Assets:** 131 more CIDs.
**Risk:** Same as 4.1.
**Timeline:** 2-4 days.

### 4.3 Maps listing page scraping (all 350+ CIDs)
Once we have CIDs, each Maps place page has:
- Phone, website, hours, reviews, photos
- Sometimes: Instagram, Facebook, Booking.com link in the "Website" section
- Place data JSON with every crawlable field

A lightweight scrape of each CID page would extract everything Maps knows
about these businesses.

**Assets:** Phone normalization, hours, reviews, social links from Maps data.
**Risk:** Low-medium — Maps page loads without search, just direct CID navigation.

---

## Phase 5 — Paid/Outsourced Options

### 5.1 Octoparse / ParseHub
Visual web scrapers with free tiers. Can schedule extractions of:
- Booking.com search results for Puerto Viejo
- Airbnb listings
- Google Maps business data (via their Google Maps extractor templates)

**Requires:** Free account, local installation.
**Risk:** Offloaded from our IP — they use their own proxy pools.

### 5.2 Scrapy Cloud (Zyte)
Free tier includes ~10k requests/month. Python-based, runs on their servers.
Could handle the full Booking.com scrape and Airbnb scrape.

**Requires:** Free account, Python deployment.
**Risk:** Their IPs, not ours.

### 5.3 Bright Data / Oxylabs (paid — last resort)
Residential proxy networks. Would allow IP rotation for Google scraping.
Costs money — only if we decide Google Search is essential and pacing is
too slow.

**Requires:** Paid subscription ($10-50/month minimum).
**Risk:** Minimal — they provide residential IPs.

---

## Data Schema — What Each Field Nets Us

| Field | Source | Current | Target |
|-------|--------|:-------:|:------:|
| business_name | All sources | 615 | 615 |
| category | PVS + OSM + grid | 481 | 615 |
| area / neighborhood | PVS + OSM + grid | 481 | 615 |
| latitude / longitude | PVS + OSM + slow search | 481 | 615 |
| google_maps_cid | PVS + hex trick + slow search | 351 | 615 |
| phone | PVS + websites + maps | 399 | 550+ |
| normalized_phone | PVS + script | 393 | 550+ |
| website | PVS + websites + maps | 81 | 200+ |
| instagram_handle | PVS + guessing + scraping | 312 | 400+ |
| instagram_url | PVS + guessing + scraping | 312 | 400+ |
| facebook_url | PVS + phone search + maps | 254 | 400+ |
| booking_url | PVS + Booking.com search | 171 | 350+ |
| tripadvisor_url | PVS + TA search | 57 | 250+ |
| airbnb_url | Airbnb search (new) | 0 | 100+ |
| whatsapp | PVS + wa.me check + maps | 68 | 300+ |
| email | Websites + OSM + maps | 0 | 100+ |
| twitter_url | Twitter search (new) | 0 | 50+ |
| tiktok_url | TikTok search (new) | 0 | 50+ |
| hours | Maps listing pages | 0 | 300+ |
| price_range | Booking/Airbnb/Maps | 0 | 200+ |
| review_score | Booking/TripAdvisor | 0 | 300+ |
| review_count | Booking/TripAdvisor | 0 | 300+ |
| description | PVS + OSM | 478 | 500+ |
| operating_status | PVS + OSM | 481 | 615 |

---

## Decision Matrix

| Phase | Effort | Risk | New fields per record | Records affected |
|:-----:|:------:|:----:|:---------------------:|:----------------:|
| 0.1 PVS cache mine | 15 min | None | Phone, IG, website | ~50-100 |
| 0.2 OSM tags extract | 5 min | None | FB, email, phone | ~31-156 |
| 0.3 Crawl 81 websites | 30 min | Near-zero | IG, FB, email, WhatsApp | ~81 |
| 0.4 Hex CID recovery | 10 min | Near-zero | CID metadata | ~350 |
| 1.1 IG guessing | 2 hrs | Low | 50-100 more IG handles | ~300 |
| 1.2 IG profile scrape | 1 hr | Low-medium | Email, website from bios | ~312 |
| 2.1 FB by phone | 1 hr | Low | 100+ FB URLs | ~250 |
| 2.2 WhatsApp verify | 30 min | None | 200+ WhatsApp confirmations | ~399 |
| 2.3 Twitter search | 30 min | Low | 50+ Twitter URLs | ~615 |
| 2.4 TikTok search | 30 min | Low | 50+ TikTok URLs | ~615 |
| 3.1 Booking.com | 2 hrs | Low | 150+ booking URLs + reviews | ~206 |
| 3.2 Airbnb | 1 hr | Low | 100+ Airbnb URLs | ~150 |
| 3.3 TripAdvisor | 1 hr | Low | 200+ TA URLs | ~393 |
| 4.1 Slow search (grid) | 3-8 days | Moderate | CID, coords, phone for 134 | 134 |
| 4.2 Slow search (CIDs) | 2-4 days | Moderate | CIDs for remaining 131 | 131 |
| 4.3 Maps CID scrape | 2 hrs | Low | Phone, hours, website | ~350 |

---

## Recommended sequencing

**Day 1 (2 hrs, zero risk):**
- Phase 0.1: Mine PVS cache SQLite
- Phase 0.2: Extract OSM contact tags
- Phase 0.3: Crawl 81 websites
- Phase 0.4: Hex CID recovery
- Phase 2.2: WhatsApp verification

**Day 2 (2 hrs, zero-low risk):**
- Phase 1.1: Instagram handle guessing
- Phase 2.1: Facebook by phone search
- Phase 2.3: Twitter discovery
- Phase 2.4: TikTok discovery

**Day 3 (2 hrs, low risk):**
- Phase 1.2: Instagram profile scraping
- Phase 3.1: Booking.com bulk lookup
- Phase 3.2: Airbnb search

**Day 4 (2 hrs, low risk):**
- Phase 3.3: TripAdvisor search
- Phase 3.4: Expedia/Hotels.com/Agoda
- Phase 4.3: Maps CID page scrape

**Days 5-14 (ongoing, moderate risk):**
- Phase 4.1: Slow stealth search for 134 grid names (8-12/day)
- Phase 4.2: Slow search for missing CIDs (8-12/day)

**Optional:**
- Phase 5: Evaluate Octoparse free tier for Google Maps extraction template
