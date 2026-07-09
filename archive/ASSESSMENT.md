# Puerto Viejo Business Discovery — Full Data Assessment

**Date:** 2026-07-06
**Total candidate pool:** 615 records across 3 source files

---

## 1. Dataset Overview

| Source | Records | Coordinates | CID | Phone | Instagram | Website | Completeness |
|--------|:-------:|:-----------:|:---:|:-----:|:---------:|:-------:|:------------:|
| PVS Master | **450** | 100% | 78% | 83% | 67% | 13% | **High** |
| OSM Additions | **31** | 100% | 0% | 68% | 26% | 61% | Medium |
| Grid Scan | **134** | **0%** | **1%** | 4% | 3% | 2% | **Very Low** |
| **Total** | **615** | **78%** | **57%** | **65%** | **51%** | **13%** | |

**Completeness score distribution** (9 = fully enriched, 0 = name only):

- Score 7-9: 320 records (52%) — the well-enriched PVS core
- Score 4-6: 156 records (25%) — partial enrichment
- Score 0-3: **139 records (23%)** — mostly the grid names, barely started

---

## 2. What's Complete

### PVS Master (450 records) — Phase 1 results
- 450 business names, categories, areas, coordinates ✅
- 350 Google Maps CIDs (78%)
- 372 phone numbers (83%), all normalized
- 300 Instagram handles, all verified working via Playwright
- 252 Facebook URLs
- 171 Booking.com affiliate links
- Operating status for all 450
- Full descriptions for 447

This is the **solid foundation**. The data is accurate as of the PVS crawl date (2026-07-03) and Instagram verification (2026-07-04).

### OSM Additions (31 records)
- All 31 have exact coordinates
- 21 phone, 19 website, 8 Instagram verified
- 31 descriptions (from OSM tags)

---

## 3. What's Outstanding

### Grid Names (134 records) — CRITICAL GAP
**134 businesses visible on Google Maps but not in our dataset.** We have names only:

| Missing | Count | Impact |
|---------|:-----:|--------|
| Coordinates | **134** | Cannot map, no geometry for dedup |
| CIDs | **133** | Cannot link to Maps, no enrichment source |
| Phone | 128 | No contact method |
| Website | 131 | No web presence link |
| Instagram | 130 | No social media |
| Area label | 134 | Unknown which neighborhood |

These are the **highest priority**. Without coordinates and CIDs, they're unusable for most analysis.

### PVS Master refinements
| Gap | Count | Opportunity |
|-----|:-----:|-------------|
| Missing CID | 100 | Could be found via slow stealth search |
| Missing phone | 78 | Possibly on Maps listings we never checked |
| Missing Instagram | 150 | Either has no IG or handle wasn't guessed correctly |
| Website (real) | 59 | 391 entries have only affiliate/tracking links |
| Facebook | 198 | Missing entirely |
| Booking.com | 279 | Missing (mostly non-hotel categories) |
| WhatsApp | 382 | Missing — hard to find without Maps data |
| Email | 450 | **No email for any record** |

### OSM Additions refinements
- All 31 missing CIDs (31 searches, ~1 hr of slow browsing)
- 23 missing Instagram (could try handle guessing)
- 29 missing Facebook
- No Booking, TripAdvisor, WhatsApp, or email for any

---

## 4. Opportunity Assessment

### Tier 1 — Highest value, highest ROI

| Opportunity | Target | Records affected | Estimated time | What it nets |
|-------------|--------|:----------------:|:--------------:|--------------|
| **Slow stealth Google search → Maps extraction** | Grid names | **134** | 3-5 hrs | CID, coords, phone, website, IG, FB, hours Booking/Airbnb |
| Same for OSM missing CIDs | OSM additions | 31 | ~1 hr | CID + deeper enrichment |
| Same for PVS missing CIDs | PVS master | 100 | ~3 hrs | Fills remaining CID gaps |
| **Full slow search run** | **All sources** | **615** | **12-22 hrs** | **Complete dataset with perfect CID coverage** |

### Tier 2 — Medium value

| Opportunity | Records | Time | What it nets |
|-------------|:-------:|:----:|--------------|
| Website scraping (81 real sites) | 81 | 30 min | IG, FB, email from business websites |
| Instagram handle guessing | ~300 without IG | 2 hrs | Auto-generate candidates, verify |
| Facebook phone-number search | ~254 without FB | 1 hr per batch | FB pages via phone search |

### Tier 3 — New discovery

| Opportunity | What it finds | Time |
|-------------|--------------|:----:|
| OSM Overpass refresh | New OSM-only businesses missed last time | 5 min |
| TripAdvisor area search | Tour companies, restaurants not in any source | 1 hr |
| Booking.com/Airbnb by area | Vacation rentals, hotels | 2 hrs |
| Tourist directory crawl | Sodas, small shops from tourism sites | 1-2 hrs |

---

## 5. Recommendations

### Short-term (< 1 day)
1. **Resolve the 134 grid names** via slow stealth browser search → CID + coordinates. This turns 134 unusable names into real records.
2. **Crawl the 81 real websites** for IG/FB/email (30 min script).

### Medium-term (1-3 days)
3. **Mop up missing CIDs** on PVS master (100) + OSM (31) via same stealth search.
4. **Refresh Instagram verification** on all 450 PVS handles — some may have died since July 4.

### Long-term (3-7 days)
5. **Full stealth search pass** on all 615 records — enrich everything to maximum depth.
6. **Cross-platform discovery** — Booking.com, Airbnb, TripAdvisor for businesses we're still entirely missing.
7. **Merge all sources** into a single unified `pv_master_v2.csv` with the 34-column schema.

---

## 6. Current File Inventory

| File | Records | Status |
|------|:-------:|--------|
| `pv_within_5km_enriched_b.csv` | 450 | Complete — the canonical master |
| `pv_within_5km_verified_additions_enriched.csv` | 31 | Needs CID resolution |
| `grid_discoveries_ig_enriched.csv` | 134 | Needs everything |
| `CODEX_ENDPOINT/tasks/osm_scanner/` | — | Working directory for bridge outputs |
| `screenshots/` | 255 PNGs | Evidence, ~250 MB |
| `neighborhood_scanner/` | — | Reusable grid + dedup modules |
| `grid_discoveries.csv` | 134 | Clean names list |
| `grid_discoveries_deduped.csv` | 251 | Grouped variants |
| `vision_results.json` | — | Raw Codex vision output |
