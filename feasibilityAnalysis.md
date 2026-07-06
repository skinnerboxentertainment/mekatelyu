# Feasibility Analysis: Autonomous Local-Business Discovery

> **Project**: Discover businesses within 5 km of Puerto Viejo de Talamanca, Costa Rica + identify Instagram accounts
>
> **Source plan**: `requestForSolutions.md`
>
> **Date**: 2026-07-03

---

## 1. Target Scope

| Dimension | Value |
|-----------|-------|
| Geographic area | 5 km radius (~78.5 km²) from 9.6554°N, 82.7533°W |
| Estimated businesses | **350–500** (OSM: ~395 POIs; Cybo: ~340+ listed) |
| Business categories | Accommodation (~27%), Food & drink (~25%), Shops (~19%), Services (~15%), Tours/attractions (~8%), Other (~6%) |

The area is a small tourist town (~350–500 businesses). This is a feasible scale for a single-machine, zero-budget project.

---

## 2. Data Source Feasibility

| Source | Feasibility | Est. Coverage | Key Risk |
|--------|------------|---------------|----------|
| **OpenStreetMap / Overpass** | ✅ Very high — free, no rate limits, no ToS issues | ~60–75% of formal businesses | Informal/micro businesses not mapped |
| **Google Maps scraping** (Playwright + stealth) | ✅ High at this scale — 50–60 searches/hour works with zero issues | ~70–85% (limited by ~60-result cap per search) | CAPTCHAs, IP blocks if scaled too fast |
| **Business websites** | ⚠️ Medium — many small businesses have no site or use Instagram only | ~40–60% | Link rot, no-index pages |
| **Instagram discovery** | ❌ Major challenge — no free API; unauthenticated search heavily restricted | Unreliable (est. 30–50% in best case) | Login gates, rate limits, GraphQL churn |
| **Tourism directories** | ✅ High — several local sites exist | ~30–50% | Stale data |

---

## 3. The Instagram Problem — Decisive Bottleneck

**Instagram account discovery is the weakest link in the plan.**

- **Instagram Graph API** requires a Facebook app, business verification, and `instagram_basic` permission — not feasible for a tool scraping random businesses.
- **Unauthenticated scraping**: Instagram blocks most search endpoints without login. Even with login, rate limits are severe (~200 actions/hour before temporary blocks).
- **Google-indexed Instagram pages**: Some business profiles are indexed — you can find `instagram.com/businessname` via search. But this is passive, not active discovery.
- **Realistic Instagram hit rate** without API access: **30–50% of businesses** at best (mostly handles that appear on Google Maps profiles, websites, or tourism directories).

**Honest assessment**: The plan's Instagram-discovery requirement is the difference between a *doable* project and a *highly speculative* one.

---

## 4. Architecture Feasibility by Approach

### 4a. Conservative / Terms-Conscious

- **Relies on**: OSM + tourism directories + manual website visits + Google-indexed Instagram
- **Coverage**: ~40–50%
- **Runtime**: ~4–8 hours (mostly automated)
- **Instagram hit rate**: ~20–30%
- **Legal risk**: Minimal
- **Verdict**: ✅ **Feasible immediately**. Safe but incomplete.

### 4b. Browser-Agent / Google Maps Interactive

- **Relies on**: Playwright browsing Google Maps, extracting listings, then cross-referencing for Instagram
- **Coverage**: ~60–75%
- **Runtime**: ~2–4 hours (automated)
- **Instagram hit rate**: ~30–40% (from Google Maps profiles + website links)
- **Legal risk**: Low–moderate (ToS gray area)
- **Verdict**: ⚠️ **Feasible with caveats**. Google Maps part works; Instagram discovery remains weak.

### 4c. Hybrid / Maximum Coverage

- **Relies on**: All sources + Instagram login + social graph crawling + possible browser automation
- **Coverage**: ~70–85% (optimistic)
- **Runtime**: ~6–12 hours
- **Instagram hit rate**: ~40–60% (best case)
- **Legal risk**: Moderate–high (Instagram ToS violation if automating with login)
- **Verdict**: ❌ **Overpromises**. Instagram discovery at scale via automation is extremely fragile. "Maximum coverage" label is misleading.

---

## 5. Critical Failure Modes

| Failure Mode | Likelihood | Impact | Mitigation |
|-------------|-----------|--------|------------|
| Google Maps blocks IP | Low at this scale | Medium | Use residential IP, random delays, headless=false |
| Instagram restricts / rate-limits | High | High | Accept lower coverage; fall back to Google-indexed handles |
| OSM has stale / delisted businesses | Medium | Medium | Cross-reference with Google Maps freshness |
| Small / informal businesses invisible online | High | High | Cannot solve without ground-truth survey; document as known gap |
| Business renamed but same location | Medium | Low | Track by lat/lon, not just name |
| Manual review burden too high | Medium | Medium | Target ≤2 hours manual review for 500 records |

---

## 6. Cost Reality Check

The prompt says "zero-cost or effectively free." This is **mostly true**:

| Resource | Cost | Notes |
|----------|------|-------|
| Compute (existing laptop/desktop) | $0 | — |
| Residential electricity | ~$0.50–$1.00 | Negligible |
| OSM / Overpass API | $0 | Unlimited free tier |
| Instagram access | $0 | But effectively crippled without API |
| Proxy rotation | $0 | Not needed at this scale |
| **Total direct cost** | **~$0–$1** | ✅ Achievably free |

The hidden cost is **engineering time** — expect **15–30 hours** to build a robust system.

---

## 7. Recommendation

**Do not pursue Instagram-first discovery.** It will consume ~80% of effort for ~30% of results.

Instead:

1. **Phase 1 — Pilot**: OSM dump + Google Maps scraping (Playwright) + tourism directory harvest. Target: 300–400 businesses with ~30–40% Instagram coverage from public sources.
2. **Instagram as enrichment, not core**: Scrape only Instagram handles already linked from Google Maps profiles and business websites. No social-graph crawling. Accept lower coverage.
3. **Ground truth** (optional): One person walking the main streets (Puerto Viejo center, Cocles, Chiquita) for 4 hours would catch 90%+ of businesses — compare against the automated set to measure recall.

---

## 8. Summary

| Question | Answer |
|----------|--------|
| Is the plan feasible overall? | **Partially** |
| What works? | OSM, Google Maps scraping, tourism directories — all at zero cost |
| What is overpromised? | Instagram discovery — expect 30–50% hit rate without API access |
| Most viable architecture? | **4b (Browser-Agent)** — best balance of coverage, cost, and risk |
| Most risky feature? | Automating Instagram with login (architecture 4c) |
| What would change feasibility? | A free or cheap Instagram search API; a ground-truth walking survey |
