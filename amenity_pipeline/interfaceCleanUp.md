I randomly selected and inspected these three pages at a 390×844 mobile viewport:

- Bendita Comida — restaurant
- Azania Bungalows — hotel
- Automotriz Danny — services

I reviewed their initial load, expanded Hours, expanded Details, and expanded Amenities where available. No changes were made.

## Overall verdict

The core mobile layout is healthy:

- No horizontal overflow
- Header remains compact
- Typography is readable
- Chips wrap correctly
- Weekly-hours tables fit cleanly
- Details convert to a usable single-column layout
- Sticky actions remain available
- Progressive-disclosure controls work
- Pages load quickly and appear visually stable

The pages are not malformed. The most important problems are data consistency, information placement, and component inconsistency—not the fundamental responsive structure.

## 1. Bendita Comida

### What works

- The initial viewport presents identity, rating, location, Hours, Details, description, and primary actions without feeling excessively long.
- Eight highlighted details are a reasonable summary.
- Expanding the 27 details produces a readable grouped list.
- The partial weekly schedule is presented honestly.
- The missing Sunday schedule is not fabricated.

### Problems

The Hours provenance line is crowded:

```text
From Google Maps · Captured 2026-08 · some days unavailable America/Costa_Rica
```

Issues:

- There is no clear delimiter before the timezone.
- `America/Costa_Rica` looks like an internal database value.
- “Some days unavailable” and the timezone compete with the provenance.

The expanded table uses inconsistent weekday labels:

```text
Monday
Tuesday
...
Saturday
Sun
```

Use `Sunday`, not `Sun`, to match the remaining rows.

The expanded status says:

```text
Hours as listed
```

That is accurate but vague. A clearer partial-data message would be:

```text
Weekly hours · Sunday unavailable
```

or:

```text
Hours listed for 6 of 7 days
```

### Recommended Bendita treatment

```text
HOURS
From Google Maps · Updated August 2026
Costa Rica time

Weekly hours · Sunday unavailable

Monday       6 AM–5 PM
...
Sunday       Not listed
```

## 2. Azania Bungalows

### What works

- This is the most balanced page of the sample.
- The amenity summary is useful and compact.
- The description appears quickly.
- Contact actions and map are not buried.
- There is no empty Hours section when weekly hours are unavailable.
- Expanding from five to seven amenities does not overwhelm the page.

### Problems

The Amenities disclosure has different styling from Hours and Details.

Collapsed:

```text
View all 7 amenities
```

Expanded:

```text
Show less
```

The expanded `Show less` control appears like a small default rectangular button, while Hours and Details use larger rounded controls with arrows. This makes the page feel assembled from separate component systems.

The expanded label should also retain context:

```text
View fewer amenities ▲
```

rather than the generic:

```text
Show less
```

### Recommended Azania treatment

Use the same disclosure component for all expandable sections:

```text
View all 7 amenities ▼
View fewer amenities ▲
```

The same component should govern:

- Hours
- Amenities
- Details

It should share:

- Border radius
- Padding
- Font size
- Arrow placement
- Hover behavior
- Focus behavior
- Expanded-state semantics

## 3. Automotriz Danny

This page exposed the most important issues.

### Contradictory operating status

The header says:

```text
Open
```

The new Hours section says:

```text
Closed now ·
```

Only one status should exist, derived from the verified weekly-hours dataset.

The trailing separator is also malformed:

```text
Closed now ·
```

Render either:

```text
Closed now
```

or:

```text
Closed now · Opens Monday at 7 AM
```

Never render the separator without following content.

### Contradictory Sunday data

The weekly table says:

```text
Sunday  7 AM–5 PM
```

The business description says:

```text
Open daily except Sunday.
```

This is a source-data conflict. It should be detected before publication.

The database-backed schedule is newer, but the site should not silently present both claims. Recommended options:

1. Remove hours claims from manually written descriptions when verified weekly hours exist.
2. Automatically flag descriptions containing schedule language for review.
3. Treat the weekly schedule as authoritative and rewrite or suppress stale descriptive claims.

### Misplaced and suspicious classification

A `Medical` chip appears directly after the Hours table.

For an auto-repair, tire, oil-change, and towing business, `Medical` appears incorrect. It is also visually misplaced: type/quality chips should be near the category and area at the top, not between Hours and Details.

This suggests two separate fixes:

- Validate the underlying type assignment.
- Move all business-type chips into the identity block near `Services` and `Puerto Viejo`.

## Cross-page material improvements

### Priority 0: establish one source of truth for open/closed status

When verified weekly hours exist:

- Compute the current state from those hours.
- Use the listing’s timezone.
- Replace the legacy header status.
- Derive today’s intervals from the same schedule.
- Never display both legacy and verified statuses.

Recommended header states:

```text
Open · Closes at 5 PM
Closed · Opens at 7 AM
Closed today
Hours unavailable
```

Overnight businesses require careful handling:

```text
Open · Closes at 2:30 AM
Closed · Opens at 4 PM
```

### Priority 0: add a publication-time consistency validator

Flag records when:

- Header status disagrees with computed weekly status.
- Description says “closed Sunday” but Sunday has hours.
- Description contains hours that differ from verified hours.
- A non-medical business has a `Medical` type.
- A schedule has fewer than seven days.
- Duplicate or conflicting day records exist.
- A day is both closed and has intervals.
- A listing claims “open 24/7” but its schedule disagrees.

The validator should generate a review report rather than silently modifying uncertain data.

### Priority 1: unify disclosure controls

Create one component with configurable labels:

```text
View full week ▼
View less ▲

View all 7 amenities ▼
View fewer amenities ▲

View all 27 details ▼
View fewer details ▲
```

Prefer consistent phrasing:

```text
View full week
View less

View all N amenities
View fewer amenities

View all N details
View fewer details
```

The orange/green focus outlines seen after activation are accessibility features, not defects. They may be restyled, but must remain clearly visible.

### Priority 1: clean up Hours metadata

Replace:

```text
From Google Maps · Captured 2026-08 America/Costa_Rica
```

with:

```text
From Google Maps · Updated August 2026
Costa Rica time
```

For incomplete schedules:

```text
From Google Maps · Updated August 2026
Costa Rica time · 6 of 7 days listed
```

Avoid exposing raw database timezone identifiers in the interface.

### Priority 1: improve expanded Hours hierarchy

The current order is:

1. Provenance
2. Disclosure control
3. Current status
4. Weekly table

A clearer order would be:

1. Heading
2. Provenance
3. Current status
4. Weekly table or disclosure control

Collapsed:

```text
HOURS
From Google Maps · Updated August 2026

Closed · Opens at 7 AM

View full week ▼
```

Expanded:

```text
HOURS
From Google Maps · Updated August 2026

Closed · Opens at 7 AM

Monday       7 AM–5 PM
...
Sunday       7 AM–5 PM

View less ▲
```

Placing “View less” after the table may be more natural, particularly after scrolling through a long schedule.

### Priority 1: move all classification chips into the identity area

Chips such as:

- Café
- Ice Cream
- Bar
- Live Music
- Medical
- Car Rental

currently appear after the Hours section on some pages.

Move them under the primary category/area row:

```text
Automotriz Danny
Services · Puerto Viejo
Mechanic · Car repair · Towing
```

This prevents unrelated chips from visually attaching themselves to Hours.

### Priority 2: add bottom safe spacing

The sticky action bar behaves correctly, but it occupies a meaningful portion of a 390×844 screen. Ensure every business page has bottom padding equal to:

```css
sticky action-bar height + safe-area inset + 16–24px
```

This guarantees that the final row, description, map link, or collapse control can scroll completely above the action bar.

### Priority 2: refine partial-day language

For missing weekdays, use consistent full labels and explicit values:

```text
Sunday    Not listed
```

Avoid abbreviating only the missing day.

Possible status vocabulary:

- `Not listed`
- `Closed`
- `Open 24 hours`
- `Hours may differ`
- `Temporarily unavailable`

Do not treat `Not listed` as `Closed`.

## Suggested final mobile structure

```text
BUSINESS NAME
Category · Area
Type/quality chips
Rating
Address
Verified current status

────────────────

HOURS
From Google Maps · Updated August 2026
Costa Rica time

Closed · Opens at 7 AM
View full week ▼

────────────────

AMENITIES
Summary chips
View all N amenities ▼

────────────────

DETAILS
From Google Maps · Updated August 2026
Summary chips
View all N details ▼

────────────────

Description
Contact actions
Map
```

## Recommended order of work

1. Fix header-versus-Hours status contradictions.
2. Add the schedule/description consistency validator.
3. Correct suspicious type mappings such as `Medical`.
4. Move secondary classification chips into the header.
5. Unify disclosure controls.
6. Clean up provenance and timezone language.
7. Standardize missing-day labels.
8. Verify bottom safe spacing.
9. Re-run mobile QA on:
   - complete hours
   - partial hours
   - overnight hours
   - no hours
   - amenities only
   - large Details section

The current responsive foundation is good. The biggest material improvement will come from making the verified data authoritative and eliminating contradictory or semantically misplaced information.