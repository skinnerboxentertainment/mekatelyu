# Adversarial Review: Phase 2 Neighborhood Scanner

**Reviewer:** Codex  
**Date:** 2026-07-06  
**Scope:** Architecture analysis only; no scanner or master dataset changes

## 1. Executive summary — which approach to start with

Start with a **coverage-driven hybrid**, not either proposal as written:

1. Use the existing sparse-cell analysis plus a hex/grid of map centers to choose a small, non-overlapping pilot area.
2. Drive one persistent, headed browser at a fixed viewport and locale.
3. Capture screenshots as evidence, but extract candidate names from accessibility/DOM metadata when available.
4. Use OCR only on the map and sidebar image regions that structured extraction misses.
5. Deduplicate candidates spatially and textually, then send ambiguous cases to human review.
6. Stop or cool down on the first challenge, consent loop, abnormal blank page, or repeated navigation failure.

Do **not** begin with 350 CID pages. The 450 known businesses are poor sampling centers because they are clustered: 199 are in Puerto Viejo, 84 in Cocles, and 69 in Playa Negra. Visiting every known CID repeatedly observes the same dense neighborhoods while undersampling the actual sparse gaps. The unit of work should be a **map tile/cell**, not an existing business.

The canonical CSV confirms 350 records with a CID and 100 without one; all 450 have distinct coordinate pairs. The missing-CID records are therefore still usable as spatial evidence and candidate-resolution anchors, but they should not trigger a second class of place-card scan.

Neither DOM access nor screenshots have a predictable “lifespan.” Screenshot capture in Playwright is not an anti-bot technique. Google still observes the same browser, network requests, navigation cadence, IP reputation, storage state, and interaction regularity. A real, headed browser with human-paced, low-volume interaction may last longer than a fresh headless context making repetitive CID requests, but this is a risk reduction, not invisibility. No architecture should promise 250 successful scans before blocking.

The practical order is:

> Open data and existing OSM cross-reference → headed browser pilot → DOM/accessibility extraction plus evidence screenshot → OCR fallback → human verification

This also exposes a flaw in the original success criterion: “one genuinely missing business per zone” is not a property the scanner can guarantee. The correct criterion is measured coverage and verified precision/recall against a manually labeled sample.

## 2. Attack on Approach A — DOM scraping

### Anti-bot risks specific to this project

- **Repetition is the strongest signal.** Three hundred fifty direct CID navigations, identical viewport, identical waits, identical sidebar scrolling, and an 8–10 second interval form a machine-like sequence even if the user agent changes.
- **Randomizing the user agent per session can make the fingerprint less coherent.** A claimed browser/OS that disagrees with Chromium features, client hints, fonts, graphics, or viewport is more suspicious than one stable profile.
- **Headed versus headless is not the decisive distinction.** Automated browser properties, clean profiles, request patterns, IP reputation, interaction timing, and challenge history remain observable.
- **CID pages are not neighborhood search results.** A place card's “nearby” or “people also search for” content is ranked and personalized, not a complete geometric inventory. It can vary by locale, session, time, category, and target business.
- **DOM selectors are unstable.** `a[role="link"]` and `aria-label` collect navigation, ads, directions, reviews, categories, and controls as well as place names. Google can change component structure without changing the visible page.
- **Body-text fallback is structurally unsafe.** It turns addresses, categories, ratings, hours, UI labels, review snippets, and the known source business into candidate businesses. A 3–80 character rule cannot establish entity type.
- **Scrolling changes the experiment.** Lazy loading, virtualized lists, recycled nodes, and ranked pagination mean a DOM snapshot is neither a stable nor exhaustive result set.
- **A direct place card may not expose the sidebar assumed by the original spec.** Lat/lon map views, CID place cards, and category searches are different products and produce different panels.
- **A CAPTCHA is not the only block condition.** Consent loops, degraded/empty maps, generic error panels, redirects, unusually sparse results, or HTTP-success pages missing expected landmarks must all count as failures.
- **The proposed runtime is internally inconsistent.** A mandatory 8–10 seconds between 350 page loads alone is 47–58 minutes. Rendering, consent handling, scrolls, screenshots, retries, and checkpoints make a 45–55 minute total unrealistic.
- **One screenshot per CID is excessive evidence.** At 350 heavily overlapping centers it adds storage without proving unique geographic coverage.

### Realistic lifespan

There is no defensible number of pages. A clean IP/session might finish a low-volume pilot or might be challenged early. The risk ordering, all else equal, is approximately:

1. fresh headless contexts with rapid, repetitive direct navigations — highest risk;
2. headed automation with repetitive direct navigations — still high;
3. one persistent headed session with low-volume, irregular, meaningful interaction — lower risk;
4. manual browsing — lowest automation risk, still subject to service limits.

DOM reads do not themselves create a special server-visible request, but the scripted browsing that produces the DOM does. Conversely, taking a screenshot does not conceal that browsing.

### Verdict

DOM/accessibility extraction is the best **text sensor** when the page is already open, but the original 350-CID traversal is a poor **sampling design** and a fragile primary pipeline.

## 3. Attack on Approach B — screenshot/OCR and computer-use fragility

### Screenshot/OCR is not an anti-bot boundary

If Playwright launches and navigates Chromium, changing the final extraction from `locator.text_content()` to `page.screenshot()` does not change most server-visible behavior. Computer-use may make interactions more human-like, but regular mouse paths, exact zoom sequences, fixed dwell times, and hundreds of repeated sessions remain automation.

### Coordinate automation is not viable as the primary control method

Fixed `(x, y)` clicks fail when any of these changes:

- viewport size, display scaling, browser chrome, or Windows DPI;
- sidebar width, map/sidebar layout, responsive breakpoints, or translated labels;
- cookie/consent banners, update prompts, sign-in prompts, tooltips, surveys, or place cards;
- browser resize, maximization state, download bar, or unexpected navigation;
- Google changes the zoom control position or hides it;
- the pointer click lands while tiles are still moving.

Use semantic locators and keyboard shortcuts for control where possible, even if extraction is visual. Before every action, assert a state landmark and take a recovery screenshot on failure. Fix viewport and device scale factor, disable browser zoom changes, and record both map zoom and browser zoom. Coordinate clicks should be a last-resort operation relative to a detected element bounding box, never absolute screen coordinates.

Popup handling must be a state machine, not a one-time “Accept all” click:

```text
expected map
  ├─ consent → handle once, re-check
  ├─ sign-in prompt → dismiss if possible, re-check
  ├─ challenge/login wall → stop session; do not bypass
  ├─ blank/error/degraded map → retry once after cooldown
  └─ unknown overlay → save evidence and queue human review
```

### Zoom drift

Mouse-wheel increments are not a stable map-zoom API. Wheel delta, pointer location, animation, browser zoom, and focus can alter the outcome. Prefer URLs with an explicit `@lat,lon,zoomz` view when they resolve consistently, then visually verify the zoom indicator/scale. If keyboard `+`/`-` is used, first reset to a known URL zoom and verify after each step. Never infer current map zoom solely by counting clicks.

### OCR weaknesses on Maps

- Place labels are small and anti-aliased; compression and high-DPI resampling damage character boundaries.
- Diacritics and multilingual names create variants: `Caméléon`, `Cameleon`, and OCR substitutions.
- Icons, roads, neighborhoods, beaches, attractions, UI text, prices, ratings, and category chips all look like short text entities.
- Labels can overlap or be truncated, and lower-priority businesses are intentionally not rendered.
- OCR finds pixels, not place identities. It generally cannot provide a CID, exact coordinate, category, or reliable entity boundary.
- Sidebar text is much easier than map-label text. Curved road labels and low-contrast map labels are substantially harder.
- Multiple OCR engines do not create independent truth; they often share the same unreadable source.

The proposed storage calculation is plausible only for compressed screenshots. A 1400×800 PNG containing map imagery may be materially larger than 200 KB. Measure actual files before budgeting.

### Verdict

Screenshots are valuable evidence and OCR is a useful fallback sensor. Treating OCR as the primary discovery mechanism produces an expensive list of strings with weak identity and coordinates. It does not solve exhaustive discovery.

## 4. Recommended hybrid fallback chain

### Stage 0 — establish a gold set

Manually label 10–15 representative tiles across Puerto Viejo, Cocles, Playa Negra, Playa Chiquita, Punta Uva, and Hone Creek. For every visible candidate, record label text, approximate map location, zoom, and whether it is a business. This is the only honest basis for measuring recall and false positives.

### Stage 1 — free/open-data candidates

Use the already present `osm_data.json`, `crossref_osm.py`, and OSM-only CSV as candidate sources. Refreshing OSM data, if later authorized, is a separate acquisition task. Open data will be incomplete, but it cheaply supplies stable coordinates, names, tags, and dedup anchors without Google browser risk.

### Stage 2 — coverage-driven browser pilot

- Select 12–20 target cells, weighted toward the commercially plausible sparse cells and boundary areas.
- Use one persistent, headed, logged-out profile at 1400×800, fixed locale and DPI.
- Navigate by explicit lat/lon/zoom, not by known-business CID, unless a CID is needed to validate a candidate.
- Wait for a stable visual state rather than a fixed delay.
- Capture the map crop and, where present, the result/sidebar crop.

### Stage 3 — structured extraction

Read visible place names, destination URLs/CIDs, accessible names, and available coordinates from rendered elements. This is not a separate browsing pass. Keep provenance: element role, text, URL, center, zoom, screenshot, and crop bounding box.

### Stage 4 — OCR fallback

Run OCR only on screenshots or regions where structured extraction yielded no candidate despite visible labels. Save raw OCR output and bounding boxes; never promote an OCR string directly into the directory.

### Stage 5 — candidate resolution

Resolve in this order:

1. exact CID/place identity, if present;
2. normalized phone or URL, if later collected from an allowed source;
3. normalized name plus close spatial distance;
4. conservative fuzzy name plus compatible category and area;
5. otherwise, retain as an unresolved candidate.

Store aliases under one candidate entity. Do not delete the raw observed forms.

### Stage 6 — human review and stopping

Human-review:

- OCR-only candidates;
- candidates without an anchor coordinate;
- fuzzy matches near the decision threshold;
- conflicting names at the same location;
- screenshots with overlap, truncation, challenge, or uncertain state.

Stop the browser session on a challenge or two consecutive degraded loads. Do not “fall back to OCR” on a CAPTCHA screenshot: it contains no business data and continuing may worsen blocking.

### Stage 7 — pilot gate

Proceed beyond the pilot only if the labeled sample demonstrates acceptable candidate recall and precision. Suggested gates:

- at least 90% precision for auto-accepted candidates;
- no OCR-only candidate auto-accepted;
- manual-review volume is operationally manageable;
- marginal unique discoveries per additional tile/zoom remain worthwhile.

## 5. Concrete zoom strategy

### Sampling centers

Build a hexagonal or staggered grid over land within the 5 km study radius. Prioritize the approximately 17 commercially plausible sparse cells, then commercial corridors and area boundaries. Remove ocean, protected jungle, and implausible cells before browsing. Known coordinates can help estimate density but should not each become a scan.

### Zooms

Pilot **z16 and z17** at every selected center:

- **z16:** broader context and larger establishments; useful for coverage.
- **z17:** denser local labels and smaller establishments; primary discovery level.

Use **z18 only on dense commercial tiles** where z17 has visibly overlapping/suppressed labels or where the gold set shows meaningful incremental recall. Use **z15 only as an orientation/QA image**, not as a primary business-extraction level. The proposed unconditional z15–z18 sweep wastes work because adjacent zooms and centers repeat most labels.

These levels are starting hypotheses, not universal facts. Calibrate them with the gold set. The minimum set is whichever of `{z16, z17}` achieves the best verified marginal recall; retain both only if each adds meaningful unique candidates.

### Tile spacing and overlap

Choose center spacing from the measured map ground footprint at the fixed viewport, with roughly 15–25% overlap. Do not guess it from zoom alone because sidebar width and latitude affect visible ground area. Save the viewport bounds with every observation so geographic coverage is auditable.

### Deduplication

Maintain two layers:

- **Observation:** raw label, OCR/DOM source, bounding box, center, zoom, screenshot, timestamp.
- **Candidate entity:** canonical name, aliases, best location, category, identity keys, confidence, and linked observations.

Normalize names using Unicode NFKD for a comparison key while preserving the original spelling; case-fold; normalize whitespace and punctuation; remove only a controlled list of geographic suffixes. Do not blindly remove meaningful words such as `Cocles` when they distinguish branches.

Cluster observations when:

- CID or canonical place URL matches; or
- normalized names match and inferred coordinates are within a conservative radius; or
- fuzzy similarity is high **and** location/category evidence agrees.

`Le Caméléon`, `Le Cameleon`, and `Le Cameleon - Cocles` may be aliases of one entity, but text alone is insufficient. Spatial agreement or a stable identity key is required. A short generic name such as `Soda`, `Caribe`, or `Tours` must never be merged by fuzzy text alone.

Track the set of contributing tiles and zooms. Re-observation increases evidence; it does not create another discovery.

## 6. OCR recommendation and expected accuracy

### Engine

Use **PaddleOCR** locally as the primary engine if installation works on the consumer Windows machine. It provides text detection, recognition, orientation handling, and bounding boxes and is generally better suited than plain Tesseract to small scene text. Keep **Tesseract** as a lightweight second opinion for clean sidebar crops, not as the primary map-label detector.

Preprocess by:

- preserving native-resolution PNG;
- cropping map and sidebar separately;
- rendering/capturing at device scale 2 if performance permits;
- upscaling small map crops 2× before recognition;
- trying limited contrast/sharpening variants while retaining the original;
- masking known UI regions;
- retaining OCR confidence and bounding boxes.

### Expected accuracy

Do not publish a single accuracy percentage before testing local screenshots. A reasonable engineering expectation is:

- **sidebar, large clean horizontal text:** high character accuracy, often sufficient for candidate generation;
- **clear map labels at z17/z18:** moderate candidate recall with meaningful spelling errors;
- **small, overlapped, low-contrast, truncated, or stylized labels:** poor and unpredictable recall.

End-to-end **business discovery recall will be lower than OCR character accuracy** because Google does not render every business, labels are suppressed, and entity classification can fail. An initial planning assumption of 70–90% usable transcription for clearly visible sidebar names and 40–75% for clearly visible map business labels is defensible only as a benchmark range to validate, not a promised result. Overall tile recall may be substantially lower.

### Filtering non-business text

Use positive and negative evidence rather than a text blacklist alone:

- mask fixed UI rectangles;
- reject known controls/categories (`Restaurants`, `Hotels`, `Directions`, `Nearby`, ratings/hours patterns);
- classify OCR regions by map position and nearby place-marker icon;
- reject road, neighborhood, beach, river, and administrative labels when identifiable;
- prefer text also seen in structured elements or at multiple zooms;
- require spatial/category corroboration for auto-acceptance;
- route uncertain strings to review.

A blacklist will drift with locale and UI changes. Keep its matches in the raw observation log for audit.

## 7. Scale feasibility — time, storage, compute

### The proposed 350 × 4 plan

It is feasible as a batch on a consumer Windows machine, but inefficient and riskier than necessary.

- **Navigation pacing alone:** 350 × 8–10 seconds = 47–58 minutes.
- **Four zoom transitions, stabilization, crops, OCR, scrolls, retries, and checkpoints:** realistically several hours, potentially 4–8 rather than 2–4 depending on tile rendering and CPU OCR.
- **OCR:** local inference can be parallelized after capture because it does not generate Google traffic.
- **Storage:** 1,400 × 200 KB is about 280 MB, but real lossless map PNGs can push the run into roughly 0.5–2+ GB. Crops, preprocessing variants, logs, and retry images add more.
- **Memory:** do not retain all images/models/results in memory. Use a bounded OCR queue.

Storage and compute are not the primary constraint; observation quality and Google traffic are.

### Recommended scale

Run a 12–20 tile calibration pilot at z16/z17, then expand only if marginal yield justifies it. A grid covering gaps should require far fewer unique centers than 350 clustered CIDs. Save one full evidence screenshot per tile/zoom and targeted crops for candidate observations; do not save multiple full-screen preprocessing variants.

### Parallelization

- **Browser acquisition:** one worker/session initially. Do not parallelize Google browsing from the same IP merely to reduce wall time; concurrency raises burstiness and complicates challenge detection.
- **OCR:** 1–2 CPU workers or one GPU worker, benchmarked locally.
- **Dedup and report generation:** parallelizable offline.
- **Human review:** batch by confidence and geographic cluster.

Use producer/consumer separation: browser capture writes immutable jobs; offline OCR consumes them. Backpressure the browser if the OCR queue or disk grows. Checkpoint per tile, not every 20 businesses.

## 8. Third approaches missed

### 8.1 OpenStreetMap/open-data reconciliation

This is the strongest third approach already present in the repository (`osm_data.json`, `crossref_osm.py`, `pv_osm_osmonly.csv`). It supplies entity-like records with coordinates and tags, which is categorically more useful for deduplication than OCR strings. Its weakness is incomplete/local stale coverage, so it complements rather than replaces visual discovery.

### 8.2 Search by category over a spatial grid

Google Maps surfaces businesses through category searches more directly than passive labels around a CID. A limited manual/browser pilot can query categories such as lodging, restaurant, café, tour, shop, and services at selected gap centers. This may improve recall but multiplies queries and therefore traffic risk. It should be tested on the gold set, not scaled speculatively.

### 8.3 Human-assisted map annotation

For a small 5 km radius, a lightweight review page showing captured tiles beside the 450 known points may outperform generalized OCR. A person clicks unknown labels; the system records screen/map position and crop. This spends human attention only where automated identity is weak and avoids pretending OCR is authoritative.

### 8.4 Maps embed iframe / Places API

- An ordinary Maps embed is a presentation surface, not a free bulk nearby-search API. Reading its content also encounters cross-origin and dynamic-rendering constraints and does not guarantee a complete result set.
- Google Places APIs are paid/keyed products and explicitly excluded by project constraints. Trying to call undocumented endpoints used by an embed merely recreates the scraping/terms/rate-limit problem with a more brittle dependency.

Therefore this is not a better free acquisition path.

### 8.5 Google My Maps exports

My Maps can export data from maps the user owns or has access to; it is not a general export of Google's business corpus for an arbitrary radius. Without an existing relevant public/user-owned map, it does not solve discovery.

### 8.6 Other open/local sources

Municipal/tourism directories, chamber listings, Facebook pages, Booking.com, and local web directories can generate candidates. Each source needs its own terms, provenance, and dedup rules. They are useful because discovery should not depend on one ranked Google view, but they are separate bounded research tasks.

## 9. Decision matrix

Scores are 1 (poor) to 5 (strong). “Anti-bot durability” means relative traffic risk, not a guarantee of access.

| Criterion | Weight | 350-CID DOM | 350-CID screenshot/OCR | Coverage hybrid | Open-data first |
|---|---:|---:|---:|---:|---:|
| Discovery recall potential | 25% | 2 | 3 | 4 | 2 |
| Entity/identity quality | 20% | 4 | 1 | 4 | 5 |
| Anti-bot durability | 15% | 2 | 2 | 3 | 5 |
| Sampling efficiency | 15% | 1 | 1 | 5 | 5 |
| Implementation robustness | 10% | 3 | 2 | 3 | 4 |
| Evidence/auditability | 10% | 2 | 5 | 5 | 4 |
| Local cost/compute | 5% | 4 | 2 | 3 | 5 |
| **Weighted total** | **100%** | **2.45** | **2.35** | **4.10** | **4.15** |

Open-data-first scores slightly higher operationally but cannot establish Google-specific visual coverage. The recommended system is therefore **open-data-first plus the coverage hybrid**, not either column in isolation.

## Final decision

Reject both full-scale proposals as currently scoped. Approve a **12–20 tile, z16/z17 coverage pilot** using one persistent headed browser, DOM/accessibility extraction when available, screenshots as evidence, PaddleOCR as a selective fallback, and human review for OCR-only candidates. Use CID pages only to resolve or verify candidate identity, and lat/lon URLs for map-centered sampling; they should not be assumed to yield the same sidebar because they represent different Maps states.

The go/no-go decision must be based on a manually labeled gold set, verified candidate precision/recall, marginal discoveries per additional tile/zoom, and observed challenge rate. If the pilot succeeds, expand the spatial grid gradually. If it fails, more screenshots and more CID visits will amplify noise and blocking rather than fix the design.
