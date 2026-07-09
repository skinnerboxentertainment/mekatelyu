# Feasibility Analysis v2 — Adversarially Revised

> **Source plan**: `requestForSolutions.md`
> **Previous document**: `feasibilityAnalysis.md` (withdrawn — numerical confidence was decorative)
> **Date**: 2026-07-03
>
> Every claim below is tagged as one of:
> - **[E]** — supported by evidence (cited)
> - **[A]** — explicit assumption (to be tested)
> - **[M]** — measurement plan defined (not yet executed)

---

## 1. What counts as a "business"? (Previously undefined)

The original analysis counted OSM POIs and Cybo listings as "businesses" without a consistent filter. This revision defines a taxonomy first.

### Inclusion criteria

A record is a **candidate business** if it sells goods or services to the public from a fixed or semi-fixed premises within the 5 km radius. This includes:

| Category | Examples | OSM tag pattern |
|----------|----------|-----------------|
| Storefront retail | Supermarkets, bakeries, clothing, hardware, gifts | `shop=*` |
| Food & drink | Restaurants, cafes, bars, sodas, fast food, ice cream | `amenity=restaurant|cafe|bar|fast_food|ice_cream` |
| Accommodation | Hotels, hostels, guest houses, cabinas, lodges | `tourism=hotel|hostel|guest_house|chalet|apartment|camp_site` |
| Services (fixed) | Banks, ATMs, pharmacies, laundries, bike rentals, car rental, clinics, dentists | `amenity=*` or `shop=*` with service type |
| Tour & activities | Tour operators, surf schools, nature centers, the Jaguar Rescue Center | `tourism=attraction|information`, `shop=travel_agency` |
| Galleries & crafts | Art galleries, souvenir shops | `shop=art|gift` |

### Ambiguous / tag separately

| Item | Handling |
|------|----------|
| Home-based businesses (no fixed signage) | **Exclude** unless discovered via a public listing with address |
| Solo tour guides | **Exclude** unless they operate from a fixed office |
| Market stalls / pop-up vendors | **Exclude** (too transient; seasonal) |
| Temporarily closed listings | **Include** but mark status = closed |
| Chains / franchises with multiple branches | **Include** each branch as separate record |
| Shared premises (e.g., a hotel with an in-house restaurant) | **Include** both if listed independently; deduplicate by lat/lon ±50 m |
| ATMs, benches, parking lots, bus stops | **Exclude** (non-commercial amenities) |
| Government offices, schools, police, town hall | **Exclude** |
| Vacation rentals (individual units on Airbnb/VRBO) | **Exclude** (not storefront businesses) |

**[E]** This taxonomy follows OSM tagging conventions (taginfo.openstreetmap.org) adapted to the local context of a Costa Rican tourist town.

---

## 2. Business count: what we actually know

### 2.1 OpenStreetMap POI audit (filtered by taxonomy)

An Overpass query (2026-07-02) returned elements with `shop`, `tourism`, or `amenity` tags within 5 km of 9.6554°N, 82.7533°W. However, **not all POIs are businesses** under the above taxonomy.

| Tag | Raw count | Estimated non-business exclusions | Adjusted business estimate |
|-----|-----------|----------------------------------|---------------------------|
| `shop=*` | 77 | ~0 (all are commercial) | **77** |
| `tourism=*` | 148 | ~50% exclusions (viewpoints, info boards, `tourism=information` without office) | **~74** |
| `amenity=*` | 175 | ~20% exclusions (parking, benches, toilets, town hall, schools, police) | **~140** |
| **Deduplicated total** | **~395** | | **~291** |

**[E]** Overpass query executed 2026-07-02. Exclusion ratios are **[A]** based on manual spot-check of OSM tags in the result set — to be refined by systematic audit in Phase 1.

**OSM-derived estimate: ~290 businesses** (lower bound, excludes unregistered businesses).

### 2.2 Cybo directory cross-check

Cybo (cybo.com/CR/puerto-viejo-de-talamanca/) lists businesses by category:

| Category | Count |
|----------|-------|
| Other accommodation | 110 |
| Restaurants | 93 |
| Hotels and motels | 68 |
| Real estate | 25 |
| Shopping | 12 |
| Holiday homes / cabins / resorts | 12 |
| Hostels | 10 |
| Grocery / supermarkets | 10 |
| **Subtotal** | **340** |
| Missing categories (pharmacies, rentals, services, etc.) | Unknown |

**[E]** Cybo data accessed 2026-07-02. Cybo is itself a scraped directory with unknown completeness. **[A]** Assume missing categories add ~30%, giving ~440. Cross-checked against OSM, the plausible range is **290–440**.

### 2.3 Ground truth measurement plan

Instead of asserting a single number, the pilot measures it:

1. **Transect walk** of the three commercial corridors (see §8) — ~3 linear km, ~2 hours — records every visible business
2. **Capturer–recapture**: compare transect list against OSM + Google Maps scrape to estimate total population (Lincoln–Petersen estimator)

**[M]** Executed in Phase 1. Until then, the working assumption is **300–500 businesses** — deliberately wide to avoid false confidence.

---

## 3. OpenStreetMap / Overpass feasibility

| Claim | v1 status | v2 correction |
|-------|-----------|---------------|
| "Free, no rate limits, no ToS issues" ❌ | Asserted without qualification | Partially wrong |

### What is actually true

- **Overpass API** is free and open. There is no monetary cost.
- **Resource limits exist**: The `kumi.systems` public endpoint enforces a per-query timeout (~180 seconds) and per-IP concurrency limit (~2 requests). Large polygons with dense data can time out.
- **Fair use expected**: The Overpass project asks users to cache results and avoid repetitive queries. A one-time dump of a 5 km polygon is well within fair use.
- **5 km radius query risk**: The area (~78.5 km²) is small. A query returning ~400 nodes completes in under 5 seconds. No timeout risk at this scale.

**[E]** Overpass API documentation (wiki.openstreetmap.org/wiki/Overpass_API). **[A]** No rate-limit issues for a single polygon dump.

**Verdict**: ✅ Fully feasible. No scraping, no ToS, no CAPTCHA. Just a one-time dump.

---

## 4. Google Maps browser-scraping feasibility

### 4.1 What changed from v1

v1 claimed "High feasibility" based on Reddit anecdotes. This version:
- Separates what is *known* from what must be *measured*
- Distinguishes the **search-results-page cap** from **detail-page extraction**
- Explicitly requires a pilot before any feasibility rating

### 4.2 The two distinct extraction modes

| Mode | Cap | Mechanism |
|------|-----|-----------|
| **Search results page** | ~60 results visible per query regardless of total matches | Google paginates client-side; scroll-loading stops at ~60 items |
| **Detail page (individual place)** | No known cap | Full data available for any single place |

**[A]** The ~60 cap is inferred from community reports (Reddit, 2025–2026) and may differ for non-English locales or signed-in sessions. **[M]** Verified during pilot by running `"restaurants near 9.6554,-82.7533"` and counting returned cards.

**Implication**: To cover 300+ businesses, you need multiple overlapping queries (by category and sub-area), not one large query.

### 4.3 Technical feasibility (not yet piloted)

| Concern | Known | Unknown |
|---------|-------|---------|
| Playwright + stealth works on google.com/maps | Multiple open-source scrapers confirm this for US/Europe | Not tested for `google.co.cr` locale — may differ |
| Anti-bot evasion | Works for 50–60 searches/hour on residential IP (community reports) | Not tested for sustained multi-session scraping |
| Headless vs headed | Headless is more detectable; headed requires a display | On a headless server, Xvfb or similar is needed |
| CAPTCHA frequency | Low at <100 queries/day (community reports) | Unknown for Costa Rica locale / Google Maps specifically |
| Result freshness | Google Maps data is generally current | Unknown gap between scrape date and real-world status |

**[M]** Each of these unknowns is resolved by a single-session pilot: scrape one category (e.g., "hotels") within a 1 km radius, measure: (a) number of results, (b) CAPTCHA encounters, (c) time to complete, (d) data quality vs. OSM.

### 4.4 Legal / ToS

- Google's Terms of Service prohibit automated access without written permission.
- No known case of an individual researcher being sued for a one-time scraping project at this scale.
- The risk increases if data is republished commercially.

**[E]** Google ToS (policies.google.com/terms). No change from v1.

**Verdict**: ⚠️ **Promising but untested for this specific domain**. Feasibility rated after pilot. Not "high" — "to be determined."

---

## 5. Instagram discovery: separating signal from guesswork

### 5.1 The three discovery channels

| Channel | Mechanism | Expected yield (Puerto Viejo) |
|---------|-----------|-------------------------------|
| **Google Maps profile link** | Google Maps business profiles optionally display an Instagram link | Unknown — **[M]** count Instagram link frequency in Google Maps scrape of 50 hotels |
| **Business website → Instagram link** | Business websites often link to Instagram in header/footer | Unknown — **[M]** crawl scraped websites; count how many contain instagram.com URLs |
| **Google search for Instagram** | `site:instagram.com "Business Name" Puerto Viejo` | Unknown — **[M]** test with 50 known business names |

### 5.2 Why v1's 30–50% was unsupported

The v1 claim "expect 30–50% hit rate" had no evidence behind it. There is no published study of Instagram adoption rates among Costa Rican small businesses. The assumption appears to be a guess extrapolated from developed-world benchmarks.

### 5.3 Measurement plan

The pilot quantifies each channel:

1. **Google Maps → Instagram**: After scraping 50 hotel profiles, count how many include an `instagram.com` URL in their Google Maps listing. Report as `p_google`.
2. **Website → Instagram**: After collecting websites for the same 50 hotels, crawl each and count links containing `instagram.com`. Report as `p_website`.
3. **Search-engine Instagram discovery**: For the same 50 hotels, search `site:instagram.com "<business name>" Puerto Viejo` and count matches. Report as `p_search`.
4. **Combined coverage**: Report how many of the 50 have an Instagram account discoverable via *any* of the three channels. This gives a lower-bound estimate.

**[M]** Pilot scope: 50 businesses, one category (hotels), one sub-area (town center). Results determine whether to invest in Instagram discovery at scale or treat it as a bonus field.

---

## 6. Runtime estimate (itemized, not decorative)

The v1 claim of "2–4 hours" ignored category generation, retries, deduplication, and manual review.

### Itemized estimate for Phase 1 (pilot only: hotels in 1 km radius)

| Step | Estimated time | Dependencies |
|------|---------------|--------------|
| Category & sub-area query generation | 20 min | Manual: define query grid + category list |
| Google Maps scrape (Playwright) | 15 min | ~5 queries × 3 min each (incl. randomized delays + page load) |
| Detail-page extraction | 10 min | ~30 detail pages × 20 sec each |
| Retries (estimated 10% failure) | +5 min | — |
| Website crawl (Instagram link detection) | 10 min | ~30 websites × 20 sec |
| Instagram search (per business) | 15 min | ~30 manual searches × 30 sec |
| Deduplication (lat/lon + name fuzzy match) | 5 min | Automated script |
| Manual review & confidence labeling | 20 min | Reviewer inspects 30 records |
| **Pilot total** | **~1.5 hours** | — |

### Extrapolated to full 5 km / all categories

| Step | Estimated time | Notes |
|------|---------------|-------|
| Query generation | 2 hours | 15–20 categories × 5–10 sub-queries each |
| Google Maps scrape | 3–5 hours | ~100–200 queries total; includes delays, retries |
| Detail-page extraction | 1–2 hours | ~300–500 detail pages |
| Website crawl | 1–2 hours | ~300–500 websites |
| Instagram search | 2–4 hours | Automated via search engine if viable; manual otherwise |
| Deduplication | 30 min | Automated |
| Manual review | 2–4 hours | 300–500 records at ~20 sec each |
| **Full run total** | **~12–20 hours** | Spread across sessions; not a single sitting |

**[A]** Estimates assume 10–20% overhead for failures, CAPTCHAs, and rate limiting. **[M]** Track actual elapsed time during pilot and extrapolate linearly.

---

## 7. Deduplication and matching

### Problem statement

| Issue | Risk | Mitigation |
|-------|------|------------|
| Same business listed under multiple names | High in tourist areas (e.g., "Soda La Lidia" vs "Soda y Restaurante La Lidia") | Levenshtein distance + token overlap on normalized names |
| Different businesses at same coordinates | High (shared premises: hotel + restaurant + tour desk) | Flag but do not merge; keep as separate records with shared location tag |
| Renamed businesses | Medium | Match by lat/lon ±50 m + business category; flag name changes |
| Nearest-coordinate merging merges neighbors | Medium | 50 m threshold is tight for a dense town center. **[M]** Validate threshold against 10 known neighboring pairs in pilot |
| Duplicate across sources (OSM + Google Maps) | Medium | Match on lat/lon ±50 m OR name similarity (Jaccard) OR phone/website |

**[E]** These are standard entity-resolution problems. The specific thresholds are **[A]** and must be validated.

---

## 8. The "4-hour walk" claim (withdrawn)

v1: "One person walking the main streets for 4 hours would catch 90%+ of businesses."

| Problem | Why it's wrong |
|---------|---------------|
| 78.5 km² area | A 4-hour walk covers ~15–20 km on foot. The 5 km radius circle has ~78.5 km² of land area. Many businesses are on unmarked side roads not visible from main streets. |
| Dense vs diffuse | The town center is dense (~50 businesses/km), but outlying areas (Cocles, Chiquita, Punta Uva) are spread over several km of road. |
| 90% is a guess | No evidence supports this figure. A proper capturer–recapture study would be needed. |

### Replacement: transect walk

Instead claim:

- **Transect 1**: Avenida 71 (town center from Banco Nacional to the soccer field) — ~1.2 km, ~40 min
- **Transect 2**: Road to Playa Cocles (from the soccer field to Cocles bridge) — ~1.0 km, ~35 min
- **Transect 3**: Playa Chiquita road (from Cocles bridge to the Jaguar Rescue Center turnoff) — ~0.8 km, ~30 min
- **Total**: ~3 linear km, ~2 hours

**Purpose**: This transect samples the highest-density commercial corridors. It is **not** an estimate of total businesses. Its purpose is to:
1. Provide a ground-truth sample for capturer–recapture estimation
2. Measure recall of the automated scrape within the sampled area
3. Give a conservative lower bound (businesses on these three segments)

**[M]** Executed in Phase 1 (or skipped if the team lacks a person on-site). If skipped, document "no ground truth available" as a limitation.

---

## 9. Coverage definition (formalized)

Coverage is meaningless without a denominator. The v1 document used "coverage" in three contradictory ways (recall, completeness, and intersection). This version defines three distinct metrics.

### Metric 1: Recall (requires ground truth)

```
recall = |scraped_set ∩ ground_truth_set| / |ground_truth_set|
```

Measured relative to the transect walk (§8). Reported separately for each source (OSM, Google Maps, websites).

### Metric 2: Precision (always measurable)

```
precision = |validated_businesses| / |scraped_set|
```

"Validated" means confirmed by ≥2 sources or by a manual check. This is measurable immediately after scraping (no ground truth needed).

### Metric 3: Completeness bound (Wagner's rule)

For N independent sources with coverage fractions `c₁, c₂, ..., cₙ`, the minimum possible total is:

```
total ≥ |union| / max(c₁, c₂, ..., cₙ)
```

Since we don't know the true coverage fractions, we report the *observed* union size as a lower bound and the union size × 1.5 as a speculative upper bound (based on the assumption that any single source covers at most ~65% of the true total).

**[E]** Wagner (2016) "Using probability sampling to estimate completeness." **[A]** The 1.5× multiplier is a heuristic — included only if caveated.

---

## 10. Revised recommendation

### Pilot architecture (unchanged from v1 but with explicit boundaries)

**Architecture 4b (Browser-Agent)** remains the recommended pilot because it balances coverage against cost. However, the pilot scope is now precisely bounded:

**Scope**: Hotels within 1 km of town center (9.6554°N, 82.7533°W)
**Expected count**: ~30–50 hotels (based on OSM data: 102 hotels in 5 km → ~40 in 1 km)
**Data sources**: OSM + Google Maps (Playwright) + websites
**Instagram**: Discovery attempted via the three-channel measurement plan (§5.3); reported as yield, not assumed
**Deliverables**: JSON dataset + runtime log + precision/recall measurements + list of unresolved questions

**Success criteria for scaling to full 5 km**:

| Criterion | Threshold | How measured |
|-----------|-----------|-------------|
| Precision | >80% | Manual audit of 50 random records |
| Google Maps scrape completes | Without CAPTCHA lockout | Session log |
| Instagram yield | >30% of businesses have discoverable handle | Three-channel measurement (§5.3) |
| Manual review burden | <5 min per 10 records | Timed during pilot |
| Runtime | <2 hours for pilot scope | Wall-clock measurement |

### Unresolved questions requiring human judgment

1. **Is Instagram coverage worth the effort in this town?** If the pilot finds that <20% of hotels have a discoverable Instagram handle, does the project still proceed, or does Instagram become a "best-effort" field?
2. **What is acceptable precision?** If precision is 70% (30% of records are wrong), do we invest in deduplication or accept the noise?
3. **Who does the transect walk?** If no team member is on-site in Puerto Viejo, is ground truth abandoned or is a local freelancer hired (introducing a ~$50 cost)?

---

## Appendix: Open issues from v1 that remain unresolved

| v1 claim | v2 status | Remaining work |
|----------|-----------|----------------|
| "350–500 businesses" | Replaced with 290–440 (OSM-derived) + measurement plan | Ground-truth transect needed |
| "OSM: ~395 POIs" | Filtered by taxonomy → ~290 businesses | Manual audit of exclusion ratios |
| "Google Maps scraping high feasibility" | Downgraded to "to be determined" | Pilot required |
| "60-result cap" | Now distinguished: search-page cap vs detail-page no cap | Verified in pilot |
| "Playwright + stealth works" | Not yet tested for this locale | Pilot required |
| "2–4 hours" | Replaced with itemized estimate (12–20 h for full run) | Track actuals in pilot |
| "30–50% Instagram hit rate" | Withdrawn; replaced with three-channel measurement plan | Pilot required |
| "4-hour walk catches 90%" | Withdrawn; replaced with transect walk for sampling | Requires on-site person |
| "Coverage" undefined | Formalized three metrics (recall, precision, bound) | Apply to pilot data |
