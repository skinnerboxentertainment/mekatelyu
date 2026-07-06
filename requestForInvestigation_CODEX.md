# Request for Investigation: Puerto Viejo Satellite Deep Analysis

**Target**: `https://www.puertoviejosatellite.com/`

**For**: CODEX investigation agent

**Date**: 2026-07-03

---

## Background

We are building an autonomous system to discover all businesses within 5 km of Puerto Viejo de Talamanca, Costa Rica, along with their Instagram accounts. Puerto Viejo Satellite (PVS) is a community-maintained directory that appears to contain most of the data we need — business names, categories, areas, phone numbers, websites, Instagram handles, Facebook links, and Google Maps references.

Before we build a crawler, we need precise answers about the site's structure, data quality, and coverage gaps.

---

## Investigation Tasks

### 1. Inventory the Complete Site Structure

**Goal**: Produce a complete map of all listing pages.

| Question | Why it matters |
|----------|----------------|
| How many category pages exist? (Hotels, Restaurants, Shopping, Services, Tours, Real Estate, etc.) | Need to enumerate all entry points for crawling |
| How many individual business listing pages exist per category? | Estimate total crawl size |
| How are listings paginated or lazy-loaded? (The category pages show `img/loading.gif`) | Determine crawling strategy |
| Is there a `sitemap.xml` or `robots.txt`? | Could provide a direct index of all pages |
| Are there Spanish-language versions of all pages? (`/es/` path) | Might double the crawl or be redundant |
| Does the site have RSS, JSON, or API endpoints? | Could simplify extraction |

**Deliverable**: A table of all category pages with estimated listing counts per page.

---

### 2. Analyze Individual Listing Page Structure

**Goal**: Determine HTML structure for data extraction.

Pick 5–10 individual listing pages across different categories and areas. For each, document:

| Data Field | CSS Selector / HTML Pattern | Present? (Y/N) | Format |
|------------|----------------------------|---------------|--------|
| Business name | (e.g., `h1`, `.entry-title`) | | |
| Category | (e.g., breadcrumb, URL pattern) | | |
| Area/Neighborhood | (e.g., `span.area`, URL pattern) | | |
| Phone number | | | |
| Website URL | | | |
| Google Maps link | (e.g., `https://maps.google.com/?cid=...`) | | |
| Instagram link | (e.g., `instagram.com/...`) | | |
| Facebook link | | | |
| Description | | | |
| Photo URL | | | |
| Verified date | (e.g., "Verified 2026-05-15") | | |
| Operating status | (e.g., "Closed" label) | | |
| Nearby businesses list | | | |

Also check:
- Are Instagram links consistently in the "Listing Details" section, or can they appear elsewhere?
- Are there any hidden fields in HTML comments or JSON-LD?
- Do the "View on map" links (`javascript:void(0)`) contain any geographic data in onclick attributes?

Example pages to inspect:
- `/en/puerto-viejo/chinuk-boutique-hotel/` (hotel with Instagram)
- `/en/puerto-viejo/gigi-o-restaurant/` (restaurant, supporter)
- `/en/playa-negra/banana-azul/` (hotel in Playa Negra)
- `/en/cocles/tasty-waves-cantina/` (restaurant in Cocles)
- `/en/puerto-viejo/old-harbour-supermarket/` (supermarket)
- `/en/closed/` (any closed listing page)

**Deliverable**: CSS selector map for all extractable fields, including confidence (high/medium/low) per field.

---

### 3. Count Instagram Coverage

**Goal**: What fraction of listings have a discoverable Instagram handle?

| Question | Method |
|----------|--------|
| How many listing pages contain `instagram.com` URLs? | Crawl 50–100 random listing pages and count |
| Do some categories have higher Instagram coverage than others? | Compare hotels vs. restaurants vs. shopping vs. services |
| Are Instagram links always in the "Listing Details" section, or also in descriptions? | Check both locations |
| Is there an Instagram field that's sometimes empty vs. always absent? | Check the HTML structure for empty icon placeholders |

**Deliverable**: Instagram coverage percentage per category, with sample size noted.

---

### 4. Geographic Filtering

**Goal**: Determine how to filter businesses within the 5 km radius.

| Question | Method |
|----------|--------|
| Does the Google Maps "Get directions" link contain a CID that resolves to coordinates? | Check `https://maps.google.com/?cid=4032204592829800059` — does it resolve to a place page with lat/lon? |
| Do the "View on map" JavaScript links contain coordinate data? | Inspect the `onclick` attribute |
| Are there any `<meta>` tags, JSON-LD, or microdata with geo coordinates? | Check page source for `latitude`/`longitude` |
| What is the geographic extent of each area label? (e.g., "Puerto Viejo", "Cocles", "Cahuita", "Manzanillo") | Which areas are fully within 5 km, which are partially within, which are outside? |
| Can we approximate coordinates from the area label alone? | Map area labels to approximate center points |

**Map the following areas to "entirely within 5 km" / "partially within" / "outside":**

| Area | Status | Approx. distance from center |
|------|--------|-----------------------------|
| Puerto Viejo Center | | |
| Playa Negra | | |
| Cocles | | |
| Playa Chiquita | | |
| Punta Uva | | |
| Manzanillo | | |
| Cahuita | | |
| Hone Creek | | |
| Bribri | | |
| Gandoca | | |
| Sixaola | | |

**Deliverable**: A geofiltering strategy (CID resolution, coordinate extraction, or area-label mapping) with confidence rating per method.

---

### 5. Data Freshness Assessment

**Goal**: Understand how stale the data might be.

| Question | Method |
|----------|--------|
| How many listings show a verification date, and what is the range? | Sample 50 pages |
| What fraction were verified in 2026 vs. 2025 vs. earlier? | Distribution |
| Do listings without a verification date exist? | Count |
| Is the closed/needs-verification list up to date? | Check if any "closed" businesses still appear in category listings |
| What is the lag between a business closing and appearing on the closed list? | Check news items vs. closed listings |

**Deliverable**: Verification-date distribution histogram and staleness risk assessment.

---

### 6. Completeness Gap Analysis

**Goal**: Estimate how many businesses exist that are NOT on PVS.

| Question | Method |
|----------|--------|
| Overlap between PVS and OSM within the same area | Compare PVS listing names with OSM node names for Puerto Viejo Center |
| What types of businesses appear in OSM but not PVS? | (e.g., small sodas, informal shops) |
| Are there categories PVS doesn't cover? | (e.g., specific service types, informal vendors) |
| Does PVS cover the full 5 km radius or only certain areas? | Check for gaps |

**Deliverable**: Estimated recall rate for PVS vs. OSM, with a list of likely-missing business types.

---

### 7. Technical Crawl Assessment

**Goal**: Determine the technical approach for extraction.

| Question | Answer |
|----------|--------|
| Is the site server-side rendered (static HTML) or client-side rendered (JS required)? | Check if content is present in raw HTML or loaded via XHR |
| Does it use any anti-bot measures (Cloudflare, CAPTCHA, rate limiting)? | Test with sequential page loads |
| What is the URL pattern for business pages? | (e.g., `/en/{area}/{slug}/`) |
| Are there redirects or canonical URLs? | Check for edge cases |
| What HTTP status codes are returned for valid vs. invalid pages? | 200, 404, etc. |
| Is there a search endpoint that returns structured data? | Check `/en/#search` |

**Deliverable**: Technical crawl recipe (HTTP library, no browser needed? or Playwright required?).

---

## Deliverable Format

Return a structured document with:

1. **Site map** — all category pages and estimated listing counts
2. **CSS selector map** — all extractable fields per listing page
3. **Instagram coverage** — percentage by category with sample sizes
4. **Geofiltering strategy** — recommended approach with confidence
5. **Freshness report** — verification date distribution
6. **Completeness gap** — estimated recall vs. OSM
7. **Technical crawl recipe** — tools, URLs, rate limits, cautions
8. **Open questions** — anything that requires human judgment

---

## Success Criteria

The investigation is complete when we can answer "yes" to all of:

- [ ] Do we know how to enumerate all listing pages programmatically?
- [ ] Do we have CSS selectors for every data field we want?
- [ ] Do we know the Instagram coverage rate per category?
- [ ] Do we have a geofiltering approach that keeps only businesses within 5 km?
- [ ] Do we know the data freshness profile?
- [ ] Do we know what's missing (gap vs. OSM)?
- [ ] Can we recommend a specific crawl tool (requests vs. Playwright)?
