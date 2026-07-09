# Puerto Viejo Business Discovery — Executive Summary

**Status:** Full pipeline built and executed. Project grew from 450 to **615+ candidate businesses**.

---

## What we built

### 1. OpenCode ↔ Codex Bridge
A working agent-to-agent communication channel. OpenCode orchestrates; Codex executes bounded tasks (vision analysis, web search, data extraction). Files in `CODEX_ENDPOINT/`.

### 2. OSM Candidate Discovery (31 new businesses)
Mined the existing `pv_osm_osmonly.csv` — 156 OSM records sitting untouched in the repo. After dedup against the 450 known, **31 verified new businesses** with coordinates, **21 with contact info** (phones, websites). Enriched with Instagram verification.

### 3. Grid Neighborhood Scanner (134 new businesses)
The main Phase 2 deliverable:

| Step | What happened |
|------|--------------|
| Grid design | 193 land scan points across 5 km radius |
| Screenshots | Playwright captured 255 headed-browser screenshots at z16/z17 |
| Vision extraction | 52 Codex vision batches → **268 unique names** |
| Dedup | Matched against 481 known → **134 genuinely new** |
| Enrichment | Web search + Instagram verification found 6 contacts, 4 IG handles |

### 4. Supporting infrastructure
- `codex_bridge.py` — thin wrapper for agent-to-agent task delegation
- `AGENTS.md` — durable repository context for both agents
- `neighborhood_scanner/` — reusable spatial grid + extraction modules

---

## Dataset growth

| Source | Count | Method |
|--------|:-----:|--------|
| Puerto Viejo Satellite (v1.0) | 450 | Original crawl |
| OSM cross-reference | +31 | Existing repo data + web verification |
| Codex web discovery | +2 | Web directory searches |
| Grid scan (Phase 2) | **+134** | 255 Maps screenshots + Codex vision AI |
| **Total candidate pool** | **~615** | |

---

## Key outcomes

- **255 screenshots** on disk as verifiable evidence of every grid point
- **6 new businesses** with verified contact info (phone/website)
- **4 new Instagram handles** verified working
- **31 OSM candidates** with exact coordinates ready for enrichment
- **~$0** spent on APIs (no Google Maps API, no paid services)
- Full audit trail: every discovery traceable to source, screenshot, or search result

---

## What's left

1. **Merge** the 134 grid discoveries into the master enrichment pipeline (full 34-column schema)
2. **Deep-enrich** the high-value candidates (website scraping, phone normalization)
3. **Phase 3** — open data reconciliation and the Google Maps computer-use scanner for even deeper coverage
4. **Manual review** of the most promising new candidates by category/area
