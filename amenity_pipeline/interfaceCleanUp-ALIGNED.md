# Final Alignment — interfaceCleanUp Implementation Plan

Status date: 2026-08-02
Author: Oscar AF / OpenCode session
Purpose: Record the agreed plan after Codex's final review of my pushbacks.
Both sides agree on direction; this documents the refined four-commit sequence
and the two verified factual corrections.

Reference: `interfaceCleanUp.md` (Codex visual review), `interfaceCleanUp-REVIEW.md`
(my pushbacks), and Codex's response (this aligns with).

---

## 1. Independent verification of Codex's corrections

I verified both of Codex's corrections against the generated database before
accepting them:

1. **Azania Bungalows is amenities-present, hours-absent.** Confirmed — Azania
   is NOT present in `verified_hours.json`. My earlier regression matrix that
   listed it as "amenities + full hours" was wrong. Correction accepted.
2. **Automotriz Danny has full 7-day hours including Sunday 07:00–17:00**,
   which directly conflicts with the description "Open daily except Sunday."
   Confirmed. The Sunday-conflict claim is real.

Also confirmed the `Medical` root cause: the `medical` tag rule matches
`clinic`/`clínica` in `maps.subcategory`, and Automotriz Danny's stale OCR
subcategory was "clinic", so the rule fired falsely at 0.9 confidence.

---

## 2. Agreed plan — four narrowly scoped commits

### Commit 1 — Versioned taxonomy correction
- Fix Automotriz Danny (`medical` tag removed; correct automotive tag where
  supported).
- Bump `TAXONOMY_VERSION` (note: code says `2026-07-21.1`, generated JSON says
  `2026-07-28.1` — reconcile).
- Update evidence packets; rebuild generated data.
- Add focused regression test (Automotriz no longer `medical`).
- Confirm unrelated medical businesses remain classified correctly.
- No general UI or validation changes in this commit.

### Commit 2 — Operational status truth
- Suppress legacy header status when verified hours exist.
- Reuse the existing verified-hours computation (no new subsystem).
- Partial-schedule rule: compute current status only when today is known;
  today unlisted → "Hours unavailable today" (important for Bendita Comida).
- Fix the dangling "·" separator.
- Statuses: `Open · Closes at 5 PM`, `Closed · Opens at 7 AM`, overnight,
  closed today, today not listed.
- Tests with an injected `now` (never the machine clock). Fixtures: normal day,
  closed weekday, overnight, partial missing today, open 24h, no verified hours.

### Commit 3 — Publication validator
- High-signal + structural checks (ERROR severity): duplicate weekday, closed
  day with periods, invalid/overlapping interval, contradictory `open24Hours`
  (combined with closed or ordinary periods), overnight without `closesNextDay`.
- WARNING severity: fewer than seven days, description-hours disagreement,
  suspicious taxonomy relationship, legacy-status disagreement (becomes a
  regression detector after Commit 2).
- Generate a review report; never mutate source data.
- Flag the Automotriz description conflict for human review.
- Structural schedule errors fail verification; editorial conflicts warn.

### Commit 4 — Interface cleanup
- Native `<details>` for Hours, Amenities, and Details (one component, shared
  styling/labels: "View all N X ▼" / "View fewer X ▲").
- Friendly provenance: `From Google Maps · Updated August 2026` + `Costa Rica
  time` (+ `· N of 7 days listed` when partial). No raw TZ identifiers.
- Full weekday names; explicit `Not listed` (never conflated with `Closed`).
- Move classification chips into the identity area (under Category · Area).
- Bottom safe-area spacing (sticky-bar height + safe inset + 16–24px).
- Expanded Hours hierarchy: Heading → Provenance → Status → table/disclosure.
- No semantic data corrections here.

---

## 3. Agreed description-conflict policy

- Detect and flag for review; do not auto-rewrite hand-written descriptions.
- Auto-remove/regenerate only when provenance proves machine-generated text.
- Verified hours are authoritative for operational UI, not authorization to
  alter editorial copy.
- Record shape:
  ```json
  {
    "listingId": "automotriz-danny-puerto-viejo",
    "issue": "description_hours_conflict",
    "descriptionClaim": "Open daily except Sunday.",
    "verifiedSundayHours": "7 AM–5 PM",
    "action": "human_review"
  }
  ```

---

## 4. Corrected regression matrix

| Page | Purpose |
|---|---|
| Bendita Comida | Partial six-day hours (today-unlisted behavior) |
| Azania Bungalows | Amenities present, hours absent |
| Automotriz Danny | Legacy-status + description-hours conflict |
| 7 Ice Creams | Complete hours, Tuesday closed |
| Hot Rocks | Overnight schedule |
| El Sol del Caribe | Large Details dataset |
| Bohemian Monkey | Amenities plus compact Details |

(If a verified amenities-plus-hours page is needed, identify one from the
generated database rather than assuming Azania has both.)

---

## 5. Open items / decisions I flag for the build

1. **Taxonomy version reconciliation** — code constant `2026-07-21.1` vs
   generated JSON `2026-07-28.1`. Need to confirm which is authoritative and
   bump consistently in Commit 1.
2. **Automotive tag** — verify the taxonomy supports an automotive/mechanics
   tag (or whether removing `medical` leaves `local-service` only). Confirm
   with the taxonomy's tag vocabulary before assigning.
3. **Overlapping-interval validator** — define "overlap" precisely (two
   non-overnight periods where `closes1 > opens2`). Avoid false positives on
   adjacent intervals (`10:00–12:00` + `12:00–14:00` are adjacent, not
   overlapping).
4. **`open24Hours` with ordinary periods** — treat as ERROR, but confirm the
   parser never emits that combination today (it shouldn't).

These are implementation details, not direction changes. I'm aligned with
Codex's four-commit plan and proceed on that basis.
