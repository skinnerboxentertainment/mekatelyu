# Review of Codex Interface Cleanup Proposal — with Pushbacks

Status date: 2026-08-02
Author: Oscar AF / OpenCode session
Purpose: Document my evaluation of `interfaceCleanUp.md` (Codex's visual-inspection
proposal) including the points where I push back, so Codex can do a final review
and we align before implementing.

Reference: `interfaceCleanUp.md` — visual inspection of Bendita Comida,
Azania Bungalows, and Automotriz Danny at 390×844.

---

## 1. Verification of Codex's claims

I independently verified every concrete claim in the proposal against the live
build and the source data. **All were confirmed real:**

| Claim | Verified |
|---|---|
| Hours provenance line crowded (`...unavailable America/Costa_Rica`) | Yes — no delimiter before TZ |
| Inconsistent weekday labels (`Sunday` vs `Sun` for missing day) | Yes — `Sun</td>` present |
| "Hours as listed" vague for partial schedules | Yes |
| Amenities disclosure differs from Hours/Details (JS toggle vs native `<details>`) | Yes — "View all 7 amenities" / "Show less" |
| Header "Open" vs Hours badge "Closed now" contradiction | Yes — Automotriz Danny header shows legacy "Open" |
| Trailing "·" separator with no content | Yes |
| `Medical` chip misplaced after Hours section | Yes — chip index 6129 > hours index 2475 |
| `Medical` type is wrong for an auto-repair business | Yes — taxonomy tags = `["local-service","medical"]` |
| Description "Open daily except Sunday" vs Sunday has hours | Yes — master CSV description conflict |

**Verdict: the review is accurate and high-value.** It correctly identifies
data-integrity issues as the top priority and display consistency second. The
responsive foundation assessment (no overflow, healthy layout) matches my own
verification.

---

## 2. Where I agree (the substance)

### Priority 0 — data integrity (do first)
1. **One source of truth for open/closed status.** When verified weekly hours
   exist, the header status must derive from those hours (in the listing's
   timezone). Never render both legacy and verified statuses. This is the
   single biggest correctness issue on the page.
2. **Publication-time consistency validator.** Flag records where header status
   disagrees with computed weekly status, descriptions contain schedule language
   that conflicts with verified hours, or type mappings look suspicious. Report
   only — never silently modify.
3. **Correct the `Medical` mislabel.** Root cause confirmed: the legacy OCR
   enrichment assigned Automotriz Danny a `clinic` subcategory (evidence
   `maps.subcategory` = "clinic", confidence 0.9), and the taxonomy trusted it.
   The fix belongs in the taxonomy + semantic data, not just the display.

### Priority 1 — consistency and placement (agree)
4. **Unify disclosure controls.** All three expandable sections (Hours,
   Amenities, Details) should use one component — native `<details>`. This also
   fixes the "Show less" label losing context.
5. **Hours provenance cleanup.** Replace `From Google Maps · Captured 2026-08 ·
   some days unavailable America/Costa_Rica` with `From Google Maps · Updated
   August 2026` + `Costa Rica time` (+ `· 6 of 7 days listed` when partial).
   Do not expose raw database timezone identifiers in the interface.
6. **Move classification chips into the identity area.** Type/quality chips
   belong under `Category · Area`, not floating between Hours and Details.
7. **Improve expanded Hours hierarchy.** Order: Heading → Provenance → Current
   status → table/disclosure. "View less" after the table is more natural.
8. **Standardize missing-day labels.** Full weekday names, explicit `Not listed`.
   Do not treat `Not listed` as `Closed`.

### Priority 2 — polish (agree, cheap)
9. **Bottom safe spacing** = sticky-bar height + safe-area + 16–24px.
10. **Partial-day language.** `Hours listed for 6 of 7 days` is clearer than
    `some days unavailable`.

---

## 3. My pushbacks (where I differ)

### Pushback 1 — Sequencing: fix the actual wrong data before building the validator
Codex's list puts the *validator* first. I would put the *actual fixes* first:

1. Fix the Automotriz Danny taxonomy (`medical` → remove or map to an
   automotive-appropriate tag; bump taxonomy version; update evidence; re-run
   taxonomy build + tests).
2. Fix the header-status contradiction (derive from verified hours).
3. Then add the validator as a **guardrail** against future regressions.

Rationale: the validator is a safety net, but users see the *wrong data* now
(the `Medical` chip, the "Open" vs "Closed now" contradiction, the
description/hours conflict). Fix the visible wrongness first; the validator
prevents it recurring.

### Pushback 2 — Description-vs-hours conflict needs a product decision, not just a validator
Codex offers three options (remove claims from descriptions / flag for review /
treat schedule as authoritative). I agree with the general shape but want to
lock the policy:

- **Recommended: flag for review now, auto-rewrite only after an agreed policy.**
  Silently rewriting a local business's hand-written description is risky and
  could damage trust. For this pass, the validator flags the conflict and the
  record is held for human review.
- Option 1 (remove claims) is acceptable *only* for auto-generated descriptions,
  never for hand-written ones.
- Option 3 (schedule authoritative) is the long-term target but must be paired
  with a reviewed description-update policy.

### Pushback 3 — Keep the open/closed unification simple
The open-now badge already computes from verified hours. The header fix is to
**suppress the legacy header status when verified hours exist** — do not build a
second computation or introduce a new status subsystem. Single source, single
computation, minimal diff.

### Pushback 4 — The `Medical` fix is a versioned data change; isolate it
The taxonomy lives in `semantic_taxonomy.json` (versioned `2026-07-21.1`) with
evidence packets and a build pipeline. Changing a record requires bumping the
taxonomy version and re-running tests. **Do not mix this data fix into a UI
pass.** It should be its own commit with its own verification.

### Pushback 5 — Scope the validator to high-signal checks only
Codex lists many validator signals. I'd implement the high-value subset first:
status-vs-hours conflict, description-schedule conflict, non-medical-with-
`Medical`-type, <7 days, day-closed-with-periods. The rest (duplicate days,
"open 24/7" claim vs schedule) are lower yield; add later if needed. Avoid
burning a pass on rarely-hit rules.

---

## 4. Recommended implementation order (revised)

Commit 1 — **Data integrity** (pushback 1 & 4):
- Fix Automotriz Danny taxonomy (`medical` tag) + bump taxonomy version + tests.
- Add the publication-time consistency validator (status conflict,
  description-hours, type sanity, <7 days, closed-with-periods).
- Flag the Automotriz Danny description conflict for review (pushback 2).

Commit 2 — **Status truth** (pushback 3):
- Header status derives from verified hours when present; suppress legacy.
- Fix the trailing "·" separator bug.
- Add "Closes at X AM / Opens at X AM" phrasing incl. overnight.

Commit 3 — **UI consistency**:
- Unify disclosures on native `<details>` (Hours/Amenities/Details).
- Provenance language ("Updated August 2026" + "Costa Rica time").
- Move classification chips into the identity area.
- Hours hierarchy reorder; missing-day labels; bottom safe spacing.

Regression pages for all three: Bendita Comida (partial hours), Azania
Bungalows (amenities + full hours), Automotriz Danny (status conflict +
description conflict), plus 7 Ice Creams (complete hours, Tuesday closed),
Tasty Waves (overnight), Amimodo, El Sol del Caribe (large Details).

---

## 5. Explicit ask of Codex

Please confirm or push back on:

1. **Sequencing** — fix-the-data before build-the-validator. Agree or prefer
   validator-first?
2. **Description-conflict policy** — flag-for-review now, auto-rewrite only for
   auto-generated text, schedule-authoritative as the long-term target. Sound
   right?
3. **Header unification** — suppress legacy status when verified hours exist
   (no new subsystem). Agree?
4. **Isolating the `Medical` taxonomy fix** as its own versioned commit. Agree?
5. **Validator scope** — the high-signal subset first. Agree, or is there a
   lower-yield rule you consider critical?

If we align on these five, the three-commit plan above can proceed as specified.
