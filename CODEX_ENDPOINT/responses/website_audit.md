# UI/UX Audit & Redesign Proposal — Puerto Viejo Business Discovery

## Rendered visual inspection addendum

I opened the live GitHub Pages site in the in-app browser and visually inspected the rendered landing page, directory, report, and gap map.

Visual impression:

- The overall look is clean and readable, with a quiet blue-gray palette, soft white cards, and simple typography. It feels like a useful internal prototype rather than a polished public data product.
- The landing page is the weakest visual experience. It is a narrow centered list of four large links on a pale background. It loads fast and looks tidy, but it has no sense of place, no map, no data dashboard feel, and no first-screen proof that this is a geographic discovery project.
- The directory feels more functional. The header, filters, category pills, and cards are understandable. On the current viewport, however, the stats wrap awkwardly and the first screen is mostly stale metric copy plus filters. The map is below all rendered cards, so visually it is not part of the primary experience.
- The report has the most polished "dashboard" feel because of the large metric cards, but those cards prominently amplify the wrong 450-record story. The first viewport is dominated by stale numbers.
- The gap map is visually effective as an operational scanner. The dark interface, full map, grid labels, and green/red markers communicate the tool's purpose quickly. It is the clearest geographic page, though it feels stylistically separate from the rest of the site and still says 450 mapped businesses.

Rendered-page issues to fix:

- Header stat wrapping on the directory creates visual clutter: values and labels split across multiple lines in a way that reads as accidental.
- The directory card list renders all 754 businesses immediately; this creates a long page where the map toggle is buried below the initial results.
- The landing page link cards are horizontally roomy but semantically flat. "Browse Directory", "Interactive Report", "Full Dataset", and "GitHub Repository" all receive similar weight even though Browse Directory should be the primary action.
- The report's two-column metric card grid is readable, but on the inspected viewport the first screen is almost entirely numeric cards. This would work well once the numbers are current and accompanied by a brief version/source statement.
- Gap map grid labels are visually dense. They work for analysis, but the page needs a selected-cell panel to make the "scanner" interaction feel complete.

## 1. Executive summary

The site already has the right raw ingredients: a static dataset, Leaflet maps, a searchable directory, an analytical report, and a gap-scanning view. The main issue is that the public story has not caught up with the dataset. The landing page, directory header, report metrics, and gap map still present the project as a 450-business directory, while the current `docs/businesses.json` contains 754 records.

That mismatch is the biggest trust problem. Visitors are told one thing in the UI, then the data quietly says another. The site should reposition itself as a growing discovery dataset: 754 total records, 481 mapped records, 457 Google Maps CIDs, 521 phones, 361 Instagram handles, 328 Facebook URLs, 68 WhatsApp numbers, and 255 screenshot evidence captures.

The second issue is hierarchy. The landing page is currently a centered link list. It does not explain what the dataset is, how it was built, what changed from the original 450-record scope, or why a visitor should choose Directory vs Report vs Gap Map. It should become a lightweight dashboard/home screen with a small interactive map preview, clear version stats, source badges, and strong navigation.

The third issue is that each page behaves like a separate prototype. Directory uses `businesses.json`; Report embeds an older 450-record GeoJSON directly in the HTML; Gap Map fetches the new JSON but still says 450 businesses. The data architecture should be unified around shared static files and shared metric derivation so counts cannot drift again.

## 2. Per-page audit

### Landing page: `index.html`

What works:

- Loads instantly and is simple.
- The four main destinations are visible without scrolling.
- The project name is clear.

What does not work:

- The core metric is wrong: it says 450 businesses and 99.8% Instagram coverage, but current data is 754 records and 361 Instagram handles, about 47.9% of total records.
- It under-sells the expanded dataset. The move from 450 to 754 records is a major milestone and should be visible.
- It does not explain the difference between total records and mapped records. The public should see: 754 total, 481 geocoded/mappable.
- There is no map. For a place-based business discovery project, the first screen should show geography.
- Navigation labels are useful but not prioritized. "Browse Directory" should be the primary CTA; Report and Gap Map should be secondary analytical views.
- The GitHub link description mentions SQLite and OSM but does not mention Google Maps grid scanning, Playwright verification, or screenshot evidence.

Concrete fixes:

- Replace the one-line subtitle with a metric strip:
  - `754` business records
  - `481` mapped
  - `361` Instagram handles
  - `521` phones
  - `457` Google Maps CIDs
  - `328` Facebook URLs
- Add a compact Leaflet map preview using `businesses.geojson` or coordinate-bearing rows from `businesses.json`.
- Add a "Dataset version" line: `Expanded dataset, generated July 2026` or `Current public export: 754 records`.
- Add a short source row: `PVS crawl`, `OSM`, `Google Maps grid scan`, `SQLite cache`, `Playwright IG checks`, `255 screenshots`.
- Replace the vertical link list with three clear actions:
  - Primary: `Browse Directory`
  - Secondary: `View Report`
  - Secondary: `Open Gap Map`
  - Utility: `Download CSV`, `GitHub`

Should the landing page have an interactive map?

Yes. It should have a lightweight, non-dominant interactive map preview. The landing page does not need the full directory map controls, but it should show the place immediately: Puerto Viejo center, 5 km radius, and mapped businesses clustered by category or coverage status. This makes the project legible in under five seconds.

Recommended implementation:

- CDN-load Leaflet only on the landing page.
- Fetch `businesses.geojson` instead of embedding map data.
- Render all 481 coordinate-bearing records as small circle markers or clustered category dots.
- Keep popups minimal: name, category, area, links to Directory with query params later if implemented.
- Use `preferCanvas: true` on the Leaflet map for marker performance.

### Directory page: `directory.html`

What works:

- Fetches the current `businesses.json`, so the card list can represent all 754 records.
- Search, area filter, category pills, and Instagram filter are useful.
- Card content includes practical contact fields: Instagram, phone, WhatsApp, website, Booking.com, TripAdvisor.
- Leaflet map updates with filtered results.

What does not work:

- Header and initial result count are hardcoded to 450 even though runtime data is 754.
- Stats bar is stale: 300 Instagram, 68 WhatsApp, 171 Booking.com, 57 TripAdvisor. Current JSON confirms 361 Instagram, 68 WhatsApp, 521 phones, 457 CIDs, 328 Facebook URLs. Booking/TripAdvisor fields are not in the current JSON schema.
- Search only checks `business_name`. Users will expect search across name, category, area, phone, Instagram handle, and website.
- 134 records currently have blank category and blank area in `businesses.json`. These become awkward filters/cards and should be normalized to `Uncategorized` / `Unknown area` or hidden behind a data-quality state.
- The map toggle appears after the full card grid. On desktop, users may never reach it if the list is long. The map should be above results, beside results, or sticky/collapsible near the filters.
- The card grid renders all matching records at once. 754 cards is manageable on desktop but heavy on mobile, especially with map markers and HTML string replacement on every filter.
- Card click always calls `focusMap(lat, lon)` even when a record lacks coordinates. That can send the map to `[0,0]` for unmapped records.
- Uses emoji as core icons. This is okay for quick prototypes but inconsistent across devices and less polished than small text badges or an icon font.

Concrete fixes:

- Compute all header stats after fetch:
  - `businesses.length`
  - coordinate count
  - Instagram count
  - phone count
  - WhatsApp count
  - Facebook count
  - CID count
- Move map toggle/map directly under filters or use a two-column desktop layout:
  - Left: filters + results
  - Right: sticky map
- Add filter options:
  - Has coordinates / no coordinates
  - Has phone
  - Has Facebook
  - Has Google Maps CID
  - Needs enrichment / missing social
- Expand search to multiple fields:
  - `business_name`, `area`, `category`, `instagram_handle`, `phone`, `website`, `facebook_url`
- Guard `focusMap` for missing coordinates:
  - Disable "View on map" for unmapped records.
  - Show a small `No coordinates` badge.
- Add pagination or virtualized rendering:
  - First 100 records by default.
  - "Show 100 more" or client-side pagination.
- Use URL state for filters, for example `directory.html?area=Cocles&category=restaurant&ig=yes`.

### Report page: `report.html`

What works:

- Has a useful analytical structure: metric cards, map, category coverage, area distribution, data quality, OSM cross-reference, sample records.
- Tables and progress bars are easy to scan.
- The embedded map gives a strong spatial overview.

What does not work:

- Metrics are stale and internally inconsistent: header says 451, metric card says 450, map text says 450, current JSON says 754.
- The report embeds old GeoJSON directly into the HTML. This makes the page large, hard to update, and likely to drift from `businesses.json`.
- It reports "450 businesses mapped", but current GeoJSON has 481 features.
- It does not explain why total records and mapped records differ.
- Area stats include older assumptions. Current JSON has 134 blank area values and includes areas outside the original six-area story such as Cahuita, Manzanillo, Bribri, and blank/unknown.
- Category stats are stale and current JSON has 134 blank categories plus one non-normalized category value `cafe; restaurant`.
- There is no trend/version block showing the growth from the original 450-record PVS set to the expanded 754-record public export.
- It shows "Sample Records (first 30)" instead of an analytical sample. That consumes space without answering a question.

Concrete fixes:

- Stop embedding GeoJSON in `report.html`. Fetch `businesses.json` and/or `businesses.geojson`.
- Derive all report metrics in JS at page load or generate a separate `metrics.json`.
- Add top-level metric cards:
  - Total records: 754
  - Mapped records: 481
  - Google Maps CIDs: 457
  - Phones: 521
  - Instagram: 361
  - Facebook: 328
  - WhatsApp: 68
  - Screenshot evidence: 255
- Add a "Coverage funnel" section:
  - Total records -> coordinate coverage -> Google Maps CID -> phone -> Instagram -> Facebook -> WhatsApp.
- Replace "Sample Records" with:
  - "Highest-priority enrichment gaps"
  - "Unmapped records by area/category"
  - "Records missing category/area"
  - "Out-of-radius or questionable distances"
- Add clear caveats:
  - `481/754 records have coordinates and appear on maps.`
  - `Blank category/area values are retained but should be normalized before public release.`

### Gap Map: `gapmap.html`

What works:

- The concept is strong: a grid-based scanner is exactly the right visual for finding spatial coverage gaps.
- It fetches current `businesses.json`, so marker data can reflect all 754 records.
- Instagram/no-Instagram toggles are useful for enrichment work.
- Grid size selector is practical.

What does not work:

- Header still says 450 businesses mapped.
- The grid labels are based on all coordinate-bearing businesses, but the page does not clearly say the denominator is 481 mapped records, not 754 total.
- It is visually disconnected from the rest of the site: dark operational interface vs light report/directory pages. That can be okay for a scanner tool, but navigation should make its purpose clear.
- Grid distance approximation uses a fixed `0.009` degrees per km for both latitude and longitude. At Puerto Viejo latitude this is close enough for a rough scanner, but not precise. Longitude degrees differ by latitude.
- Grid cells are labels only, not clickable cells, despite the info text saying "Click a grid cell".
- The category color constant is unused because markers are colored only by Instagram status.
- There is no list of businesses in the selected cell, no export of a cell, and no "empty/low coverage" ranking.

Concrete fixes:

- Update title copy: `481 mapped businesses from 754 total records`.
- Make grid cells actual `L.rectangle` layers with click handlers.
- On cell click, populate the info panel with:
  - cell ID / bounds
  - business count
  - Instagram count
  - no-Instagram count
  - list of businesses
  - "Copy search query" or "Export cell CSV" if useful
- Add a toggle for marker coloring:
  - Coverage mode: Instagram yes/no
  - Category mode: category colors
  - Source mode: PVS / OSM / Google grid if source is exported
- Replace the rough degrees conversion with simple helpers:
  - latitude degrees per km: `1 / 110.574`
  - longitude degrees per km: `1 / (111.320 * Math.cos(lat * Math.PI / 180))`
- Add an "Empty/low-density cells" side panel sorted by count.

## 3. Landing page redesign

The landing page should become a public dashboard, not just a link directory. It should answer four questions immediately:

1. What is this?
2. How big is the dataset now?
3. Where is the coverage?
4. What can I do next?

Recommended content:

- H1: `Puerto Viejo Business Discovery`
- Subhead: `A static, evidence-backed directory of businesses around Puerto Viejo de Talamanca, expanded from the original 450-record set to 754 discovered records.`
- Metric strip:
  - `754 records`
  - `481 mapped`
  - `457 Google Maps CIDs`
  - `521 phones`
  - `361 Instagram`
  - `328 Facebook`
- Primary action row:
  - `Browse Directory`
  - `View Report`
  - `Open Gap Map`
  - `Download CSV`
- Map preview:
  - 5 km radius circle
  - coordinate-bearing businesses
  - category or coverage legend
- Source/evidence strip:
  - `PVS crawl`
  - `OSM`
  - `Google Maps grid scan`
  - `SQLite cache`
  - `Playwright verification`
  - `255 screenshots`

Specific HTML/CSS/JS recommendations:

- Use a full-width header band with constrained content, not a narrow centered page only.
- Keep the map in the first viewport, but do not make it huge. Recommended height: 320-420 px desktop, 260 px mobile.
- Use CSS grid for the hero:
  - Desktop: text/actions/stats on the left, map on the right.
  - Mobile: title, stats, action buttons, map stacked.
- Load Leaflet from CDN as currently done.
- Fetch `businesses.geojson` for the map preview; fetch `businesses.json` only if you need non-geo metrics.
- Use a `metrics.json` file if possible so the landing page does not have to derive every count.
- Add a small data-version line near the metrics: `Public export: July 2026`.

Example implementation sketch:

```html
<section class="hero">
  <div class="hero-copy">
    <p class="eyebrow">Expanded public export · July 2026</p>
    <h1>Puerto Viejo Business Discovery</h1>
    <p class="lede">754 discovered business records around Puerto Viejo de Talamanca, with mapped locations, contact channels, social links, and screenshot-backed verification.</p>
    <div class="actions">
      <a class="primary" href="directory.html">Browse Directory</a>
      <a href="report.html">View Report</a>
      <a href="gapmap.html">Open Gap Map</a>
    </div>
  </div>
  <div class="map-panel">
    <div id="landingMap"></div>
  </div>
</section>
<section class="metrics">
  <div><strong>754</strong><span>records</span></div>
  <div><strong>481</strong><span>mapped</span></div>
  <div><strong>457</strong><span>Google CIDs</span></div>
  <div><strong>521</strong><span>phones</span></div>
  <div><strong>361</strong><span>Instagram</span></div>
  <div><strong>328</strong><span>Facebook</span></div>
</section>
```

```js
const map = L.map('landingMap', { preferCanvas: true, zoomControl: false })
  .setView([9.6554, -82.7533], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OSM',
  maxZoom: 18
}).addTo(map);

L.circle([9.6554, -82.7533], {
  radius: 5000,
  color: '#e74c3c',
  fillColor: '#e74c3c',
  fillOpacity: 0.05,
  weight: 2,
  dashArray: '5,10'
}).addTo(map);

fetch('businesses.geojson')
  .then(r => r.json())
  .then(geo => {
    L.geoJSON(geo, {
      pointToLayer: (feature, latlng) => L.circleMarker(latlng, {
        radius: 4,
        color: '#fff',
        weight: 1,
        fillColor: feature.properties.instagram ? '#2ecc71' : '#95a5a6',
        fillOpacity: 0.75
      })
    }).addTo(map);
  });
```

## 4. Data architecture recommendations

### Unify public data files

Current problem:

- `directory.html` and `gapmap.html` fetch `businesses.json`.
- `report.html` embeds stale GeoJSON in the HTML.
- `businesses.geojson` has 481 features, but report copy still says 450 mapped.

Recommended public files:

- `businesses.json`: full 754-record row data.
- `businesses.geojson`: only records with valid coordinates, currently 481 features.
- `metrics.json`: precomputed counts used by all pages.
- `schema.json` or a short `data-dictionary.md`: documents fields and blank-value semantics.

Recommended `metrics.json` shape:

```json
{
  "generated_at": "2026-07-06",
  "records_total": 754,
  "records_mapped": 481,
  "google_maps_cids": 457,
  "phones": 521,
  "instagram_handles": 361,
  "facebook_urls": 328,
  "whatsapp_numbers": 68,
  "screenshot_evidence": 255,
  "sources": ["PVS crawl", "OSM", "Google Maps grid scan", "SQLite cache", "Playwright IG checks"]
}
```

### Normalize blank categories and areas

Current JSON has 134 blank categories and 134 blank areas. That creates public-facing awkwardness and weak filters.

Recommended handling:

- Keep raw values in source/master data.
- In public export, add normalized fields:
  - `category_normalized`
  - `area_normalized`
  - `has_coordinates`
  - `has_social`
  - `data_quality_flags`
- Render blank category as `Uncategorized`.
- Render blank area as `Unknown area`.
- Add a report section quantifying these gaps.

### Avoid count drift

All user-facing counts should be derived from the same static metrics file or generated at build time. Hardcoded counts should be removed from page copy.

Places currently needing replacement:

- `docs/index.html`: 450, 99.8% Instagram coverage, 450 markers, 450 records.
- `docs/directory.html`: header stats and initial "Showing 450 of 450".
- `docs/report.html`: all 450/451 report metrics, embedded older GeoJSON, category/area/data-quality tables.
- `docs/gapmap.html`: "450 businesses mapped" header.

### Performance

754 records and 481 markers are not large, but mobile performance can degrade from rendering every card and marker repeatedly.

Recommended optimizations:

- Use `preferCanvas: true` for Leaflet maps with many circle markers.
- Render only the first 100-150 directory cards, with "Show more" or pagination.
- Debounce search input by 100-200 ms.
- Cache lowercase searchable text per business after fetch.
- Reuse markers where possible instead of removing/recreating every marker on every filter.
- Lazy-load maps:
  - Landing map loads immediately.
  - Directory map loads only when visible, or after the first idle moment.
  - Report map loads when scrolled near viewport.
- Keep `businesses.json` lean. Do not include unused fields in the public JSON.
- If search grows more complex, use a CDN-sourced client search library such as MiniSearch or Fuse.js, but the current size can still be handled with plain JS.

### Search indexing

Create a precomputed field:

```js
b._search = [
  b.business_name,
  b.category_normalized || b.category,
  b.area_normalized || b.area,
  b.instagram_handle,
  b.phone,
  b.website,
  b.facebook_url
].filter(Boolean).join(' ').toLowerCase();
```

Then filter with `b._search.includes(query)` rather than only business name.

## 5. Priority-ordered action items

### P0 — Fix trust-breaking data mismatches

1. Update all visible 450/451 references to current metrics.
2. Replace `99.8% Instagram coverage` with accurate social coverage language.
3. Make Report fetch current data instead of embedding old GeoJSON.
4. Add explicit distinction between `754 total records` and `481 mapped records`.

### P1 — Make the landing page useful

5. Redesign landing page as a compact dashboard.
6. Add Leaflet map preview with 5 km radius and mapped records.
7. Add source/evidence badges and dataset version line.
8. Promote Directory as primary CTA; Report and Gap Map as secondary actions.

### P1 — Improve directory usability

9. Compute stats dynamically after loading `businesses.json`.
10. Expand search beyond business name.
11. Add filters for coordinates, phone, Facebook, Google CID, and missing social.
12. Handle missing coordinates gracefully; do not focus map to `[0,0]`.
13. Move map near filters or create a desktop split view.

### P2 — Normalize public data quality

14. Normalize blank area/category values for public display.
15. Add report sections for unmapped records and uncategorized records.
16. Add quality flags to public JSON.

### P2 — Improve Gap Map as an operational tool

17. Make grid cells clickable.
18. Show selected-cell business list and social/contact counts.
19. Add low-density/empty-cell ranking.
20. Add category/coverage/source coloring modes.

### P3 — Polish and resilience

21. Add shared nav/header across pages.
22. Add loading and error states for JSON fetch failures.
23. Add URL state for directory filters.
24. Add mobile-specific tuning for card density and map height.
25. Add a small build/check script that verifies public counts before deployment.

## 6. Mock landing layout

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Puerto Viejo Business Discovery                         GitHub  Download  │
├────────────────────────────────────────────────────────────────────────────┤
│ Expanded public export · July 2026                                         │
│                                                                            │
│ Puerto Viejo Business Discovery        ┌────────────────────────────────┐  │
│ 754 discovered business records        │                                │  │
│ around Puerto Viejo de Talamanca,      │  Interactive Leaflet preview    │  │
│ with mapped locations, contact         │  - 5 km radius                  │  │
│ channels, social links, and            │  - 481 mapped businesses        │  │
│ screenshot-backed verification.        │  - IG/no-IG or category dots    │  │
│                                        │                                │  │
│ [Browse Directory] [View Report]       └────────────────────────────────┘  │
│ [Open Gap Map]                                                             │
├────────────────────────────────────────────────────────────────────────────┤
│ 754 Records │ 481 Mapped │ 457 CIDs │ 521 Phones │ 361 IG │ 328 Facebook │
├────────────────────────────────────────────────────────────────────────────┤
│ Sources: PVS crawl · OSM · Google Maps grid scan · SQLite cache ·          │
│ Playwright Instagram checks · 255 screenshot evidence captures             │
├────────────────────────────────────────────────────────────────────────────┤
│ Directory           Report                         Gap Map                 │
│ Search/filter all   Coverage, quality, source      Grid scanner for        │
│ business records    metrics, category/area stats   coverage gaps           │
└────────────────────────────────────────────────────────────────────────────┘
```

Recommended first implementation path:

1. Generate `metrics.json` from `businesses.json` and `businesses.geojson`.
2. Update `index.html` to use `metrics.json` and `businesses.geojson`.
3. Update `directory.html` hardcoded copy and computed stats.
4. Rebuild `report.html` so all metrics derive from current data.
5. Update `gapmap.html` copy and add clickable grid rectangles.
