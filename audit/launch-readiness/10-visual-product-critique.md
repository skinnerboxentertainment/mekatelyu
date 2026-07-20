# Visual and Product Critique

Assessment date: 2026-07-20
Surfaces: live directory home, results, business detail, map/list controls, and representative 1440×1000, 390×844, and 320×568 layouts
Mode: read-only visual/interaction assessment

## Overall opinion

**Paradisio is visually coherent, legible, and more considered than a raw data project—but it still feels like a capable internal directory prototype rather than a distinctive Puerto Viejo consumer product.**

The palette is the strongest aesthetic decision. Sand, jungle green, reef, and coral suit the Caribbean setting without becoming cartoonish. Spacing, radii, surfaces, and component treatments are consistent. The product feels calm and practical.

What it lacks is a strong sense of place and a decisive visitor hierarchy. System typography, minimal imagery, metadata-heavy cards, raw taxonomy, repeated trust badges, developer modes, and owner-oriented material compete with the simple visitor promise: find a good local place and contact or navigate to it.

### Directional rating

| Dimension | Rating | Opinion |
|---|---:|---|
| Brand coherence | 3/5 | Consistent palette, but limited identity beyond color and the name |
| Sense of place | 2/5 | Little visual evidence of Puerto Viejo’s landscape, culture, people, food, or businesses |
| Desktop composition | 2.5/5 | Clean but overly linear and repetitive for the available width |
| Mobile composition | 2.5/5 | Touch-friendly foundations, but the primary task is buried and fixed controls collide |
| Information hierarchy | 2/5 | Too many labels have similar visual weight; operational metadata competes with decisions |
| Trust impression | 2/5 | Numerous “verified” signals look systematic, but inconsistencies make them feel asserted rather than earned |
| Distinctiveness | 2/5 | Could be mistaken for a well-themed generic directory |
| Launch polish | 2/5 | Prototype controls, placeholder journeys, raw labels, and content/data anomalies remain visible |

These ratings describe the audited build, not the project’s potential.

## What works

### The color system has the right emotional temperature

Warm sand surfaces and dark jungle green create a relaxed, grounded base. Coral provides energy for actions and reef green works naturally for contact/trust cues. The restrained palette avoids the loud tropical clichés common in tourism products.

### Components share a consistent visual grammar

Cards, filters, pills, buttons, and panels use a coherent 4 px spacing system, modest radii, thin borders, and soft shadows. Nothing feels randomly styled. Touch targets are generally designed around practical mobile sizing.

### The basic interaction model is understandable

Category shortcuts, search, filters, list/map switching, business cards, and direct contact actions are familiar. A visitor can infer how the product works without onboarding.

### Business pages contain useful decision material

Name, category, area, status, hours, rating, contact channels, map, description, and direct actions form a useful core. The fixed mobile contact bar is the right product instinct when unobstructed.

## Where the visual product falls short

### 1. The platform has colors, but not yet a strong identity

The name and palette carry nearly all brand expression. System UI typography is efficient but anonymous. There is no meaningful logo system, signature illustration, photographic direction, icon language, or editorial voice establishing why this is *the* Puerto Viejo guide.

This does not require a photo-heavy tourism site. A restrained local visual language—custom wordmark, region-specific graphic motif, selective business photography, authored neighborhood imagery, or small illustrated category markers—would create recognition without sacrificing speed.

### 2. The homepage delays the main visitor task

On mobile, the user encounters navigation, three language controls, masthead copy, eight category tiles, four catalog statistics, and an update timestamp before search and results. This makes the site describe itself before helping.

Search should be immediately available near the promise. Category discovery can remain prominent, but detailed inventory statistics and update metadata should not outrank intent.

### 3. Desktop does not capitalize on desktop

The main results remain a long single-column stream within an 1100 px container. It is readable, but visually monotonous and inefficient. Desktop can support a stronger browse layout: compact two-column results, a persistent filter rail, or a split list/map composition. The current layout feels like mobile expanded horizontally rather than a deliberately composed desktop product.

### 4. Cards contain too many small competing signals

A typical result can show name, stars, rating, category, area, distance, contact-strength label, multiple channel badges, “Fully Online,” and a CTA. Many are rendered with similar pills and small text. Repetition across 50 initial results creates visual noise and weakens scan speed.

The card should answer three questions in order:

1. Is this the kind of place I want?
2. Where is it, and is it open/relevant now?
3. What is the best next action?

Channel availability and internal quality scores should be compressed or progressively disclosed. One trusted status and one primary action are stronger than a row of seven badges.

### 5. Data vocabulary leaks into the interface

Labels such as `tour_company`, `vacation_rental`, and `real_estate` expose storage identifiers. Mixed capitalization (`Transport`, `Wellness`, `Nightlife` versus lowercase categories) makes the system feel unfinished. Category and subcategory copy is sometimes redundant or implausible, which becomes an aesthetic problem because visitors experience data quality as design quality.

### 6. “Verified” is overused and visually under-explained

Cards and details can combine “Verified,” “Map Verified,” “Instagram verified,” “Fully Online,” “Strong,” and freshness text. These labels occupy valuable attention without clearly defining what was verified, by whom, or when. When invalid routes or stale data appear alongside them, the visual language damages trust.

Use fewer, precise signals—for example, “Contact checked Feb 2026”—with details available on demand. Trust should feel evidential, not decorative.

### 7. Visitor, owner, and developer experiences are mixed together

The fixed Tourist/Business Owner/Premium Owner/Admin selector is unmistakably a prototype instrument. QR-sticker promotion, contactability/visibility/completeness scores, claim prompts, premium upsells, and owner tools appear within a tourist business page. These make the page feel like a demo of multiple product ideas instead of a focused visitor experience.

For the reduced directory launch, the tourist surface should be visually pure. Owner acquisition can be a quiet secondary path, and operational/development controls should be absent.

### 8. Mobile has good primitives but poor priority

The two-column category grid and filter grid are space-efficient, but together they create a dense control wall. The fixed mode selector collides with the fixed business CTA. The nav/language row also asks too much of a narrow width.

The mobile hierarchy should become:

- compact brand/navigation;
- promise plus search;
- a small set of high-intent category chips;
- results with filter/sort in a compact sheet or disclosure;
- one unobstructed sticky primary action on details.

### 9. The product is text- and badge-heavy, with little emotional reward

Directory utility is necessary, but Puerto Viejo is experiential. Business names alone cannot carry discovery. Selective, well-cropped imagery or a consistent fallback illustration system would make browsing more inviting and help distinguish restaurants, stays, tours, shops, and services. Images should be curated and optional—not an uncontrolled requirement that creates broken placeholders.

### 10. Accessibility defects are visible design defects

Faint-on-sand text (`2.54:1`) and coral-on-white text (`3.74:1`) appear intentionally subtle but become weak, especially outdoors on mobile. Lack of a strong focus treatment also reduces polish for keyboard users. Improving contrast and interaction state will make the product look more confident, not merely more compliant.

## Recommended visual direction for August 1

This is a refinement, not a redesign. Avoid introducing an untested design system during the launch window.

### P0 — Remove prototype residue

- Remove the mode selector and all public privileged-mode affordances.
- Remove payment, claim, classifieds, QR promotion, internal scores, and premium upsell from the reduced visitor release where those capabilities are out of scope.
- Replace raw category identifiers with a controlled presentation vocabulary.
- Stop displaying unreliable verification/contact badges.

### P1 — Clarify the primary hierarchy

- Put search directly beneath or inside the masthead promise on mobile and desktop.
- Reduce the homepage above-search content; move catalog statistics below results or into an About/Data page.
- Simplify result cards to name, human category, area/distance, open/freshness state where reliable, and one primary action.
- On desktop, choose either a two-column compact grid or a deliberate list/map split.
- Preserve one unobstructed sticky CTA on mobile business pages.

### P1 — Improve visual confidence

- Raise low-contrast text and action colors to accessible values.
- Add clear hover, focus-visible, active, selected, loading, and empty states.
- Establish a small icon set for category/contact types instead of relying on repeated text pills.
- Normalize casing, punctuation, date formats, distance precision, and Spanish/local naming.

### P2 — Build identity after launch safety

- Commission/refine a Paradisio wordmark and compact mark.
- Define a restrained photographic or illustrated art direction grounded in Puerto Viejo.
- Introduce optional business hero/card imagery with curated fallbacks and performance limits.
- Develop a clearer editorial voice for neighborhood discovery and local context.

## Suggested reduced-release composition

### Desktop home

1. Compact dark-green navigation with Paradisio identity and Directory/About.
2. Focused masthead: “Find trusted places around Puerto Viejo” plus prominent search.
3. Six concise category shortcuts.
4. Filter/sort row.
5. Two-column compact results or list/map split.
6. Quiet methodology/freshness footer.

### Mobile home

1. Compact brand row with one menu control.
2. Short promise and full-width search within the first viewport.
3. Horizontally scrollable high-intent category chips or four primary tiles.
4. Results immediately, with filter/sort behind two clear controls.
5. No developer mode or catalog telemetry competing with results.

### Business detail

1. Name, human-readable category, area, reliable open/freshness state.
2. One primary contact action and secondary Map/Call/Instagram options.
3. Short useful description and key amenities.
4. Map/location.
5. Quiet data-source/correction link.
6. Owner/QR/premium material omitted from tourist mode.

## Conclusion

Paradisio does not need visual reinvention before August 1. It needs subtraction, hierarchy, and truthfulness. The existing palette and component foundation are worth keeping. Removing prototype surfaces, moving search forward, simplifying cards, cleaning labels, and protecting the primary mobile action would produce the largest improvement with the lowest launch risk.

After launch safety, the next design investment should be identity and sense of place—not more controls.
