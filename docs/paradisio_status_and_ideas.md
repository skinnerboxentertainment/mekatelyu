# Paradisio — Status & Roadmap

## Built (stable)

| Area | Status | Key metrics |
|------|--------|-------------|
| 772 business pages with search/filters/map | Stable | 721 CIDs, 614 WhatsApp, 452 IG, 191 websites |
| Maps enrichment v2 + v3 parsing | Stable | 689 ratings, 564 subcategories, 437 amenities, 151 cuisines, 279 open status |
| OSM pipeline (discovery → CID → merge) | Stable | 418 scanned, 22 merged |
| Full-text corpus (2.6M chars) | Stable | Re-parseable forever — `maps_parsed_v3.json` |
| Multi-language EN/ES/DE | Stable | Client-side i18n switcher, 120 keys each |
| QR codes (print + gallery) | Stable | 772 PNGs, redirect pages |
| Classifieds board | Stable | 15 seed listings |
| Live dashboard (`watch_status.ps1`) | Stable | Real-time progress bar |
| Codex v2 ping-pong session | Stable | Strategic advisory pipeline |

## Coverage snapshot

| Field | Count | % of 772 |
|-------|:-----:|:--------:|
| Google Maps CID | 721 | 93% |
| Phone | 611 | 79% |
| WhatsApp | 614 | 80% |
| Instagram | 452 | 59% |
| Rating | 689 | 89% |
| Subcategory | 564 | 73% |
| Amenities | 437 | 57% |
| Open/closed status | 279 | 36% |
| Cuisine type | 151 | 20% |
| Address | 176 | 23% |
| Website | 191 | 25% |

## Phase 3 — Platform depth (next up)

| # | Priority | What | Effort | Why |
|--|----------|------|--------|-----|
| 1 | 🔴 P0 | **Multi-language AI audit** — run EN/ES/DE locales through Codex for quality + add FR, PT locale files | 2 hrs | Every page, immediate polish |
| 2 | 🔴 P0 | **Claim/correction form** — business owners can claim page, update hours/contact/offers | 4 hrs | Unlocks monetization, freshens data |
| 3 | 🟡 P1 | **Open-now filter** — search by "open now" from normalized weekly hours | 3 hrs | Top tourist request |
| 4 | 🟡 P1 | **Capture links+images** — update maps_enrich_v2.py to save links/images/JSON-LD per methodology | 2 hrs | Missing routing data (menus, booking, reservations) |
| 5 | ✅ DONE | **Business descriptions** — generated for all 295 businesses without them via template pipeline. Category-aware, varied by type. `paradisio_app/generate_descriptions.py` for re-use. | Done | Every page now has a description |
| 6 | 🟡 P1 | **Address coverage boost** — improve address regex to capture street addresses (currently 23%) | 1 hr | Big UX gap |
| 7 | 🟡 P1 | **Classifieds posting flow** — Web3Forms + WhatsApp-first submission | 3 hrs | Community engagement |

## Phase 4 — Monetization & Growth

| # | Priority | What | Effort | Why |
|--|----------|------|--------|-----|
| 8 | 🟠 P2 | Premium listing tiers (featured CTA, analytics pack, QR pack) | 1 week | Revenue |
| 9 | 🟠 P2 | Instagram event detection engine | 2 weeks | Flywheel fuel |
| 10 | 🟠 P2 | WhatsApp concierge (tourist-facing assistant) | 2 weeks | Direct bookings |
| 11 | 🔵 P3 | Print magazine (quarterly, QR-enabled) | Ongoing | Physical distribution |
| 12 | 🔵 P3 | Port scanner to second town | 1 week | Replicable model |

## Technical debt / watch items

| Issue | Status |
|-------|--------|
| Capture doesn't save links/images/JSON-LD per methodology | Pending Phase 3 |
| Address parser weak — 23% coverage, confuses plus codes | Pending Phase 3 |
| Hours parser weak — 8% coverage, only basic time ranges | Needs better heuristics |
| Codex session artifacts (`CODEX_ENDPOINT/responses/`) growing | Occasional cleanup |
| Biz page payload in `businesses.json` may grow large with new fields | Monitor |

---

*Generated 2026-07-11 — reflecting full session*
