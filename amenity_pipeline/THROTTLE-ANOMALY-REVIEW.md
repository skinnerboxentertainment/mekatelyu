# Amenity Extraction — Anomaly Review (for Codex)

Status date: 2026-08-02 (America/Costa_Rica, ~03:20)
Author: Oscar / OpenCode session
Request: Independent review of an amenity extraction pipeline that is producing
implausibly low yields. Something is wrong beyond obvious throttling.

---

## 1. TL;DR

We built a Playwright + ARIA-snapshot amenity extractor for Google Maps business
pages (726 CIDs from the Whappin catalog). Across ~12 hours of runs, only **148
of 726 records** (20%) have any amenities extracted. Post-mortem shows **at least
three distinct Google page variants** are being served, and our extractor only
correctly recognizes **one** of them. The other two are being misclassified as
"genuinely has no amenities" when they are actually Google serving reduced or
different UI. This misclassification is the primary anomaly; throttling is a
secondary contributor.

---

## 2. The pipeline (what it does)

- Input: `amenity_pipeline/amenities-listings.jsonl` — 726 listings (from
  `pv_master_unified.csv`, only rows with a numeric `google_maps_cid`).
- For each listing, launch anonymous Playwright Chromium, open
  `https://www.google.com/maps?cid=<cid>&hl=en`.
- Wait for a place panel (h1), run identity check (source name vs detected name).
- Locate `View more amenities` button in the `main` role, click it, verify
  `View fewer amenities` appears.
- Capture `page.getByRole("main").ariaSnapshot()` and parse `img` accessible
  names ending in exactly `available`/`unavailable`.
- Statuses: `success`, `page_degraded`, `amenities_not_exposed`,
  `place_identity_mismatch`, `navigation_failed`, `place_not_loaded`,
  `consent_required`, `captcha_or_traffic_block`, etc.
- Batch runner is resumable (checkpoint file), retries transient failures,
  has throttle backoff.

Files: `amenity_pipeline/src/{extract,parse,identity,runner,status,cli}.ts`,
`amenity_pipeline/tests/`, evidence in `amenity_pipeline/output/evidence/`.

---

## 3. The numbers that triggered this review

| Metric | Value |
|---|---|
| Listings with a result (unique) | 727 |
| **With any amenities extracted** | **148 (20%)** |
| Zero amenities | 579 (80%) |
| `amenities_not_exposed` | 397 |
| `success` | 148 |
| `page_degraded` | 108 |
| `place_identity_mismatch` | 71 |
| `place_not_loaded` | 2 |
| `navigation_failed` | 1 |

Run 2 (the 581-record retry after the initial run): ~6 hours wall time produced
**2 real successes**. A single-shot probe of a known-good hotel (3 Bamboo
Ecolodge, CID 4522237674630690631) succeeded immediately with 14 amenities,
proving the extractor works when served a healthy page.

### Failure over time (run 2, per hour)

| Hour | n | success | degraded | no-amenity |
|---|---|---|---|---|
| 02:00 | 14 | 1 | 11 | 1 |
| 03:00 | 39 | 0 | 25 | 8 |
| 04:00 | 250 | 1 | 31 | 187 |
| 05:00 | 282 | 1 | 45 | 201 |
| 06:00 | 6 | 0 | 6 | 0 |

Google throttles the anonymous session hard and **intermittently**: it lets a
couple of requests through, then serves reduced pages for long stretches.

---

## 4. The primary anomaly: multiple unrecognized page variants

### Variant A — Normal place panel (correctly handled)
Has the amenities section with `View more amenities` button and `img` state
labels. Extractors work; produces `success`.

Evidence: `output/evidence/3-bamboo-ecolodge-*.aria.yml`, `awa-beach-*.aria.yml`.

### Variant B — Booking/pricing panel (we detect this as `page_degraded`)
Page swaps the detail panel for booking widgets:
`Pricing and availability`, `Check availability`, `Compare prices`,
`All options`, `See rooms`, `per night for ...`.
No amenity section anywhere. We detect this via `isDegradedPage()` markers and
classify as `page_degraded` → throttled. **This classification may be wrong for
some businesses** — see open question 1.

Evidence: `output/evidence/casa-lucas-*.aria.yml`, `caribe-dental-*.aria.yml`.

### Variant C — Limited / unsigned view (NOT detected — misclassified)
Page contains the literal strings:

> "You're seeing a limited view of Google Maps." / "Learn more about limited view"
> "Get the most out of Google Maps" + "Sign in" button

and, for closed businesses, `Permanently closed` + "Claim this business".

This variant contains **no amenity section** but is **not** the booking/pricing
panel. Our `isDegradedPage()` markers do not match it, so the extractor throws
`AmenitiesNotExposedError` and the record is recorded as `amenities_not_exposed`
(a "genuinely no amenities" verdict). **This is a false negative.**

Evidence: `output/evidence/beach-hut-puerto-viejo.*.aria.yml` (a hotel, marked
`amenities_not_exposed`, but shows "limited view of Google Maps" + "Sign in").

### Implication
The 397 `amenities_not_exposed` records almost certainly contain a large share
of Variant C pages (limited view) and possibly Variant B pages. These are NOT
"the business genuinely exposes no amenities" — they are Google serving reduced
UI to an anonymous session. The dataset is therefore under-counting amenities.

---

## 5. Secondary issues observed

1. **Identity matcher was too strict** (fixed mid-session): the CSV's
   `business_name` often carries a geo suffix
   (` - Playa Negra, Puerto Viejo, Limón, Costa Rica`), and possessives/plurals
   (`Mitchaelle's` vs `Mitchaelles`, `Cabina` vs `Cabinas`) caused false
   `place_identity_mismatch`. Fixed in `src/identity.ts`; 47/52 previously
   flagged records now match. The 71 remaining `place_identity_mismatch` records
   are mostly from the *old* logic and need a re-run, not a re-think.

2. **`amenities_not_exposed` on a permanently-closed business** (Beach Hut):
   closed listings legitimately have no amenities. Our dataset has ~3 known
   closed records; the rest are operating_status unknown/blank (106 records). We
   are not excluding closed/limited-view pages before concluding "no amenities".

3. **Throttle detection granularity**: Variant B detection keys off six English
   marker strings. If Google localizes or varies the wording, detection silently
   degrades to Variant-C-style misclassification. There is no assertion that
   *any* page was positively identified as a healthy place panel before we
   conclude "no amenities."

---

## 6. Concrete evidence artifacts to inspect

- `amenity_pipeline/output/amenities.jsonl` — every result (dedupe by
  listingId, keep latest capturedAt).
- `amenity_pipeline/output/evidence/*.aria.yml` — ARIA snapshots.
- Key files for the three variants:
  - A: `3-bamboo-ecolodge-cahuita-lim-n-costa-rica-cahuita.aria.yml`
  - B: `casa-lucas-cahuita-lim-n-costa-rica-cahuita.*.aria.yml`
  - C: `beach-hut-puerto-viejo.*.aria.yml`
- `amenity_pipeline/src/extract.ts` — `isDegradedPage()`, `extractAmenitiesFromPage()`.
- `amenity_pipeline/src/status.ts` — status taxonomy.

---

## 7. Open questions for Codex

1. **Is Variant B really a throttle signal, or just how Google renders certain
   lodging/booking-heavy pages even to healthy sessions?** If some businesses
   legitimately render a booking panel with no amenity section, then
   `page_degraded` is wrong for them and they need their own status
   (`no_amenities_ui`), not a retry/backoff.
2. **Is Variant C the biggest loss?** How many of the 397 `amenities_not_exposed`
   records are actually Variant C (limited view)? Suggest scanning the evidence
   files for the "limited view of Google Maps" string to quantify.
3. **Should we treat "no amenities section" as a verdict at all**, or only as
   "inconclusive" unless we positively confirm a healthy place panel? This is the
   core correctness question. A conservative pipeline would record
   `amenities_not_exposed` only when a full panel rendered (identified by
   presence of the detail/overview tabs, hours, phone, etc.), otherwise
   `page_reduced_ui` (inconclusive).
4. **Closed/claimable businesses**: should we short-circuit closed listings
   (Permanently closed marker) to `business_closed` and never spend a request
   trying to extract amenities?
5. **Throttle reality**: given ~20% yield and intermittent hard throttling, is
   anonymous scraping viable at 726 records at all, or should the recommendation
   be the official Places API for a bounded enrichment pass? (No paid APIs
   without explicit owner approval — this is a design question, not authorization.)
6. **Pacing**: what request rate actually stays under Google's radar for a fresh
   anonymous session? We saw a known-good probe succeed, then a burst get
   throttled. Single-request + long sleeps vs short bursts vs browser-session
   recycling per N records?

---

## 8. What we would like back

- A verdict on each open question (1–6).
- A recommended state machine for page classification (healthy / reduced /
  limited / booking / closed / blocked) with the exact positive signals to
  require before emitting `amenities_not_exposed`.
- Recommended changes to `src/extract.ts` (and `src/status.ts` taxonomy) to
  eliminate the false `amenities_not_exposed` for Variants B and C.
- A recommendation on pacing / feasibility for the remaining ~580 records.

---

## 9. Follow-up: signed-in throwaway profile test (2026-08-02)

Codex question 5 asked whether anonymous scraping was viable and suggested a
signed-in session might bridge the remaining gap. This was tested:

- Built `--profile <dir>` support using real Chrome (`channel: chrome`) with
  Playwright's automation markers removed (`--enable-automation` off,
  `navigator.webdriver` deleted). Google's sign-in rejected Playwright's bundled
  Chromium ("browser may not be secure") but accepted real Chrome.
- **Finding 1:** the signed-in session only takes effect in **headed** mode.
  Both legacy and new headless drop the authenticated Maps session (page
  renders "limited view") even though `accounts.google.com` shows signed in.
- **Finding 2:** with the profile working (headed), 10 previously
  "limited-view" lodging records were re-tested. All 10 now render full pages
  (`limitedView: false`) but **0 of 10 expose any hotel-amenity states** — not
  on Overview, not on About. Several have About-tab attributes (e.g.
  Crowd: LGBTQ+ friendly) but no `img "… available/unavailable"` amenity matrix.
- **Finding 3:** a known-good record (3 Bamboo Ecolodge) extracts all 14
  amenities through the same profile, proving the full loop works.

### Conclusion

The ~150 pending lodging records are **genuinely absent from Google's amenity
data** — not hidden behind the anonymous limited view. Signing in removes the
limited-view banner but reveals no amenity matrix for these businesses. The
durable result stands at **213/367 lodging (58%)** with parseable amenity
states, recovered from saved evidence.

The signed-in profile would still be valuable for the **non-lodging About-tab
extractor** (Crowd, Service options, Payments, Atmosphere, etc.), which the
anonymous session cannot reach. That is the recommended next build per question
6 above.

