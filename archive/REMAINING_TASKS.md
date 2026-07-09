# Remaining Enrichment Tasks (post-Day-1)

## Completed (today)

- [x] PVS SQLite cache mined → +139 records, 12 IG refills
- [x] OSM contact tags extracted → 29 records with email/IG/FB
- [x] Website crawl (79 sites) → 12 IG, 13 FB, 15 emails, 2 WhatsApp
- [x] Grid screenshots captured (255)
- [x] Grid names extracted from vision (134)
- [x] Instagram verification on grid names (4 found)

---

## Still outstanding

### Tier 1 — Deterministic, zero risk (< 2 hrs)

| Task | What it nets | Time |
|------|-------------|:----:|
| **139 PVS cache records** — run them through IG discovery + dedup | Fill contact gaps on the new cache records | 30 min |
| **OSM Overpass refresh** — try different mirrors/methods now | More OSM-only businesses | 10 min |
| **Revisit 255 screenshots** — Codex re-exam for phone numbers, signage, URLs | Phone/website from storefronts | 30 min |
| **Merge everything** into a unified master CSV | Single 615+ record file with 34-col schema | 20 min |

### Tier 2 — Low risk, targeted (2-4 hrs)

| Task | What it nets | Time |
|------|-------------|:----:|
| **Booking.com search** for 206 lodging records | Booking URLs, review scores, pricing | 1.5 hrs |
| **Viator/GetYourGuide** for 25 tour companies | Tour platform URLs | 30 min |
| **TripAdvisor search** for restaurants (97 records) | TA URLs, review counts | 1 hr |
| **Hostelworld** for 20 hostel records | Hostelworld URLs, reviews | 15 min |
| **Instagram guessing** for ~300 without IG | Maybe 50-100 more handles with identity checks | 2 hrs |

### Tier 3 — Medium risk, careful pacing (3-8 days)

| Task | What it nets | Timeframe |
|------|-------------|:---------:|
| **Slow stealth search** for 134 grid names → CID + coords | Turns 134 name-only records into real geospatial records | 3-8 days |
| **Slow search for 131 missing CIDs** (100 PVS + 31 OSM) | CID fill for incomplete records | 2-4 days |
| **Maps CID page extraction** on all 350+ existing CIDs | Phone, hours, website from Maps listing data | 2 hrs |

### Tier 4 — Evaluate/pilot

| Task | What it nets |
|------|-------------|
| **Octoparse free tier** — test Google Maps extraction template | Offload Google risk if it works |
| **Facebook discovery** — search by phone for 250 without FB | FB pages — but risk of account flag |
| **Airbnb search** for named vacation rentals | Airbnb URLs — but listing ambiguity |

---

## Recommended next pick

**Tier 1: Merge everything into a unified master CSV.** We have data across:
- `pv_within_5km_enriched_b.csv` (450 base)
- `pv_within_5km_verified_additions_enriched.csv` (31 OSM)
- `grid_discoveries_ig_enriched.csv` (134 grid)
- `pv_cache_additions.csv` (139 cache)
- `website_enrichment_all.csv` (new emails/IG/FB)
- `osm_contact_tags.csv` (29 OSM contact records)

A single merge pass produces a **750+ record master** with the richest possible snapshot. Then we know exactly what's still missing per record.
