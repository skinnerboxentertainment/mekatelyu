# QA Triage Trail — Batch 1 (Category & Area Corrections)

**Started:** 2026-08-05
**Source of truth:** GitHub QA tickets #22–#77 (56 open, filed by Xio)
**Scope of this batch:** Category and area misclassifications verified against `pv_master_unified.csv`

---

## Summary

| Metric | Value |
|---|---|
| Open QA tickets reviewed | 56 |
| Category corrections applied (Batch 1) | 27 (19 → vacation_rental, 2 → wellness, 5 → tour_company, 1 → services, 1 → shopping) |
| Area corrections applied (Batch 1) | 4 |
| Reference points kept + recategorized (owner decision) | 3 (Arrecife El Chino, Beach Trail, Cubali Beach → tour_company) |
| Contact-link fixes applied (Batch 2) | 15 (7 IG removed, 2 IG corrected, 1 FB removed, 5 website→TripAdvisor, 3 TA affiliate cleanups) |
| #33 BERACA closure (Google permanently_closed) | 1 |
| Stale-description hygiene sweep | 33 |
| Tickets fully resolved (Batches 1–2) | 49 |
| Tickets requiring Xio follow-up | 5 (2 names, 3 empty) |
| Test suite | 74/74 PASS |
| `verify_source_data.py` | PASS |
| `verify_release.py` | PASS |
| Semantic taxonomy | regenerated, 737 records, 0 review queue |

---

## Root cause

`pv_master_unified.csv` inherited a wrong `category` for a batch of businesses
from the source PV Satellite crawl — vacation rentals ("Casa X"), wellness
centers, a night club, tour operators, and a honey shop were all classified as
`restaurant`. Xio's QA review surfaced these on the live site.

## Artifacts

| File | Purpose |
|---|---|
| `audit/qa-triage/category-corrections.csv` | Per-ticket category manifest (ticket, business, old→new, rationale) |
| `audit/qa-triage/area-corrections.csv` | Per-ticket area manifest |
| `audit/qa-triage/removals.csv` | Reference-point decisions (all `keep_recategorized`; owner approved) |
| `scripts/apply_qa_corrections.py` | Validated apply script (dry-run by default) |

## Verification method

1. Dry-run `scripts/apply_qa_corrections.py` — every precondition validated.
2. `--apply` wrote 28 changes to the master CSV atomically (before/after logged).
3. `build_semantic_taxonomy.py` regenerated the index (primary_category derives from master category).
4. `build.py` regenerated `release/` (737 pages).
5. Rendered category badge + meta description confirmed for all 24 corrected pages.
6. Full test suite + both verifiers pass.

---

## Ticket status map (all 56 open)

### FIXED — category corrected & confirmed rendered (32 tickets)

| Ticket | Business | Old | New |
|---|---|---|---|
| #25 | Abba Home | restaurant | vacation_rental |
| #27 | Api-Rescate | restaurant | shopping |
| #37 | Buddy's Sloth Crossing | restaurant | tour_company |
| #39 | Café Jaguar & Art Gallery | — | area → Playa Chiquita |
| #41 | CaribeZen | restaurant | wellness |
| #42 | Casa Alegra | restaurant | wellness |
| #43 | Casa Amor | restaurant | vacation_rental |
| #44 | Casa Antorcha | restaurant | vacation_rental |
| #45 | Casa Canopy | restaurant | vacation_rental |
| #46 | Casa Canopy | — | area → Playa Chiquita |
| #48 | Casa Chilamate Day House | restaurant | vacation_rental |
| #49 | Casa Lily | restaurant | vacation_rental |
| #50 | Casa Lily | — | area → Playa Chiquita |
| #51 | Casa Miluca | restaurant | vacation_rental |
| #53 | Casa Miluco | restaurant | vacation_rental |
| #54 | Casa Olingo | restaurant | vacation_rental |
| #55 | Casa Olingo | — | area → Cocles |
| #57 | Casa Lily | restaurant | vacation_rental |
| #58 | Casa Miluca | restaurant | vacation_rental |
| #60 | Casa Pallaita | restaurant | vacation_rental |
| #62 | Casa Shanti | restaurant | vacation_rental |
| #63 | Casa Shanti | restaurant | vacation_rental |
| #64 | casa tia zeidy | restaurant | vacation_rental |
| #65 | Casa vacacional happy day beach house | restaurant | vacation_rental |
| #66 | Casa Vosi | restaurant | vacation_rental |
| #67 | Casas Sloth & Butterfly | restaurant | vacation_rental |
| #72 | Cirrus Sky Paragliding CR | restaurant | tour_company |
| #73 | Clan Vibes Club | restaurant | services |
| #74 | Clan Vibes Club | restaurant | services |

Sweep additions (same defect, not yet QA-reviewed): Casa Amma, Casa Palliata,
Nana's Place Beach House → vacation_rental.

### KEPT + RECATEGORIZED — non-business reference points, owner decision (3 tickets)

Xio did NOT request deletion for these — she flagged them as "not a restaurant"
(reference point / trail / road). Owner decision: **keep the listings**. Per the
dataset precedent for attractions (Gecko Trail, Cacao Trails, Nature Observatorio),
recategorized `restaurant` → `tour_company` so they stop appearing as food.

| Ticket | Business | New category | Evidence |
|---|---|---|---|
| #29 | Arrecife El Chino | tour_company | Coral reef / surf break in front of Puerto Viejo (web + Maps ARIA) |
| #32 | Beach Trail | tour_company | Trail (Maps: "Activities") |
| #76, #77 | Cubali Beach | tour_company | Beach/road (Maps: "Activities"; Xio: "a road not hiking") |

Recorded in `removals.csv` (decision = `keep_recategorized`). No rows removed.

### NO DATA CHANGE NEEDED (2 tickets)

| Ticket | Business | Note |
|---|---|---|
| #28 | Aroma Coffee Bar | "Not a bar, a cafe" — cafe maps to existing `restaurant` category; no code/data change. |
| #26 | Aloe Boutique | Already `shopping` in master; ticket confirmed no change needed. |

### FIXED — contact links (Batch 2, 2026-08-05)

Verification method: Instagram OG-metadata probe (live account + owner name vs
dead/personal) via `https://www.instagram.com/{handle}/`; Google redirect
follow for Azul; rendered-page grep on rebuilt release.

| Ticket | Business | Fix | Verified |
|---|---|---|---|
| #34 | BERACA | IG `@beraca` (personal acct "Reynaldo Beraca") → `@beracacr` ("Beraca Cr") | ✅ rendered |
| #38 | Café Gustitos | IG `@caf_gustitos` (dead) → `@cafegustitos` ("CAFE GUSTITOS") | ✅ rendered |
| #36 | Bread and Chocolate | IG `@breadand` (personal acct "Álvaro Paniagua") removed; TA affiliate URL cleaned | ✅ rendered |
| #69 | Chile Rojo | IG `@chili_cr` (personal acct "Katherynne") removed | ✅ rendered |
| #47 | Casa Chilamate Day House | IG `@casachilamatedayhouse` (dead) removed | ✅ rendered |
| #30 | Azul Bar and Grill | IG `@azulbarandgrill` (dead) removed; TA affiliate URL cleaned | ✅ rendered |
| #31 | Beach Break Restaurant | FB generic `profile.php?id=` removed (IG `@beachbreak_cocles` verified CORRECT, kept) | ✅ rendered |
| #35 | Boca Chica | Website (TripAdvisor review page) → moved to `tripadvisor_url` | ✅ rendered |
| #40 | Cafe Viejo | Website (TripAdvisor) → `tripadvisor_url` | ✅ rendered |
| #68/#70 | Chile Rojo | Website (TripAdvisor) → `tripadvisor_url`. Name on Google = "Chile Rojo" (master correct); #70 FB-name is cosmetic, no change. | ✅ rendered |
| #75 | Cool and Calm Cafe | Website (TripAdvisor) → `tripadvisor_url` | ✅ rendered |
| #71 | Chill and Cheese | IG `@chillcostarica` verified EXISTS ("ChillCostaRica") — plausibly correct brand; kept, flagged for Xio | ✅ kept |
| sweep | Automotriz Danny | IG `@automotrizdanny` (dead + already `removed` confidence) removed | ✅ rendered |
| sweep | De Gustibus Bakery | Website (TripAdvisor) → `tripadvisor_url`; TA URL cleaned | ✅ rendered |

### FIXED — #61 Casa Miluca duplicate (2026-08-05)

**Verdict: NOT a duplicate.** Casa Miluca and Casa Miluco are two distinct
rentals in Playa Negra, 2.56 km apart. Google independently confirms Casa Miluco
(detected "Casa Miluco", CID 1887854985612918255); Casa Miluca has its own phone
(+506 8953 6016) and no CID. No merge.

Adjacent hygiene sweep (recorded here): 33 non-restaurant businesses carried
stale "X is a restaurant in Puerto Viejo" template descriptions (27 from Batch 1
recategorization + 6 from earlier taxonomy fixes). The live site was already
correct (build.py's `is_auto_description` regenerates short text), but the master
CSV is now clean too — all 33 regenerated for corrected category/area in
`description-corrections.csv`. Zero remaining.

### CLOSED — #52 Casa Miluca area (confirmed-correct, 2026-08-05)

Xio reported "located at Playa Negra". Master already has area=Playa Negra.
Verified, documented on the issue, and closed as confirmed-correct.

### CLOSED — Automotriz Danny #24 + #23 (resolved / duplicate, 2026-08-05)

- **#24** (had content): "says medical where it should show open hours" — both
  already fixed in the 2026-08-02 work. Verified: zero "medical" on rendered page
  (services/local-service taxonomy, commit 104516d0); full verified weekly hours
  embedded (Mon–Sat 07:00–17:00, Sun with "Virgen de los Angeles" exception,
  status open) via hours integration 81f54c1e + open-now hardening 530a3074.
  Documented and closed.
- **#23** (empty): duplicate of #24 (same business, 3 min apart). Closed as
  duplicate with an invitation to re-report if separate.

### PENDING — needs Xio clarification or owner decision

| Ticket | Business | Issue |
|---|---|---|
| #70 | Chile Rojo | FB-name differs (master name matches Google "Chile Rojo") — cosmetic, confirm with Xio |
| #22 | Aloha Skincare | Empty ticket — reassign to Xio for details |
| #56 | Casa Chilamate | Empty ticket — reassign to Xio for details |
| #59 | Casa Miluco | Empty ticket — reassign to Xio for details |
| #71 | Chill and Cheese | IG @chillcostarica kept (exists, "ChillCostaRica") — confirm with Xio it's the right brand |

---

## Next batches

- **Batch 3:** name-mismatch + duplicate tickets — reassign to Xio for clarification (data already verified correct)
- **Batch 4:** 5 empty tickets — reassign to Xio requesting issue details

## Hold state

All changes are local and **uncommitted** per owner decision ("verify locally, hold commits for review").
The release artifact has been rebuilt locally; nothing has been pushed or deployed.
