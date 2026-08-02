The proposed solution is a progressive-disclosure Details section: preserve every extracted Google attribute in the data model, but initially show only a concise, category-aware summary. Visitors can expand the section when they want the complete information.

This separates two concerns:

- Data completeness: retain all 5,748 extracted attributes.
- Interface usefulness: display only the most relevant information by default.

## 1. Default presentation

The Details section would initially contain:

- A heading
- A subtle Google Maps provenance label
- Approximately 4–8 prioritized attributes
- One button to reveal the complete dataset

Example:

```text
DETAILS
From Google Maps · Captured August 2026

Wheelchair-accessible entrance
Outdoor seating
Dine-in
Vegetarian options
Accepts reservations
Free Wi-Fi

View all 67 details
```

The summary should appear compact enough that the business description, contact actions, and map remain reasonably close to the top of the page.

The section should not show every group heading in its collapsed state. Six attributes arranged under fifteen headings would recreate much of the existing visual noise.

## 2. Expansion behavior

Activating “View all 67 details” reveals every extracted attribute, organized under the existing Google-derived groups:

```text
ACCESSIBILITY
Wheelchair-accessible entrance
Wheelchair-accessible seating
Wheelchair-accessible toilet

SERVICE OPTIONS
Outdoor seating
Delivery
Takeaway
Dine-in

HIGHLIGHTS
Great coffee
Great cocktails
Live music

OFFERINGS
Coffee
Vegetarian options
Vegan options
Wine

...

View fewer details
```

The button then changes to “View fewer details.” Collapsing should return the user to the Details heading or preserve a sensible scroll position so they are not stranded far down the page.

Use one master disclosure rather than a separate accordion for every group. Fifteen group accordions would impose too many decisions and taps.

## 3. Volume-based behavior

Not every listing needs collapsing. The presentation can adapt to the amount of data.

### 1–8 attributes

Show all attributes. Do not show an expansion button.

This works for genuinely small datasets such as:

```text
DETAILS

Sleeps 10
2 bathrooms
Minimum 3 nights
```

### 9–20 attributes

Show approximately six prioritized attributes, followed by:

```text
View all 18 details
```

This would improve the 7 Ice Creams page, where eighteen attributes currently occupy most of the initial mobile viewport.

### More than 20 attributes

Show six to eight prioritized attributes and place the complete grouped collection behind the disclosure:

```text
View all 67 details
```

The count tells users that additional information exists and sets an accurate expectation about the expansion.

These thresholds should be configuration values rather than hard-coded throughout the renderer:

```python
DETAILS_EXPANSION_THRESHOLD = 8
DETAILS_SUMMARY_LIMIT = 6
DETAILS_LARGE_SUMMARY_LIMIT = 8
```

## 4. Category-aware prioritization

The summary should not simply select the first six attributes returned by Google. It should rank attributes according to the business category and their practical value to a visitor.

### Restaurants and cafés

Recommended ordering:

1. Accessibility
2. Service options
3. Dietary or distinctive offerings
4. Dining options
5. Highlights
6. Planning
7. Parking
8. Everything else

Strong summary candidates include:

- Wheelchair-accessible entrance
- Outdoor seating
- Delivery
- Takeaway
- Dine-in
- Vegan options
- Vegetarian options
- Breakfast
- Accepts reservations
- Live music
- Free Wi-Fi

Lower-priority default candidates include:

- Casual
- Cosy
- Groups
- Tourists
- Credit cards
- Debit cards
- NFC payments

Those values remain available after expansion.

### Hotels, hostels, and vacation rentals

Verified lodging amenities should remain a distinct section because they represent explicit available/unavailable Google states.

The Details summary can prioritize other structured facts:

1. Accessibility
2. Essential accommodation information
3. Parking
4. Policies
5. Crowd or identity attributes

Example:

```text
AMENITIES
Free Wi-Fi · Free parking · Beach access · Smoke-free

DETAILS
Sleeps 10 · 2 bathrooms · Minimum 3 nights
```

There is no need to collapse that combined example because it is already concise.

### Tours

Prioritize:

- Accessibility
- Appointment or reservation requirements
- Family suitability
- On-site or online service
- Language-related information, if available
- Parking

### Shops

Prioritize:

- Accessibility
- Delivery
- In-store pickup
- In-store shopping
- Payment support
- Parking

### Services and wellness

Prioritize:

- Accessibility
- Appointment requirements
- On-site services
- Online appointments
- Restroom availability
- Parking
- Identity-related information where relevant

The rankings should live in one configuration structure:

```python
ATTRIBUTE_GROUP_PRIORITY = {
    "restaurant": [
        "Accessibility",
        "Service options",
        "Offerings",
        "Dining options",
        "Highlights",
        "Planning",
        "Parking",
    ],
    "shopping": [
        "Accessibility",
        "Service options",
        "Payments",
        "Parking",
    ],
    "services": [
        "Accessibility",
        "Planning",
        "Service options",
        "Amenities",
        "Parking",
    ],
}
```

## 5. Attribute-level ranking

Group priority alone is not sufficient. “Service options” could contain seven values, consuming the entire summary. Individual attributes need scores as well.

Example:

```python
ATTRIBUTE_PRIORITY = {
    "Wheelchair-accessible entrance": 100,
    "Delivery": 90,
    "Outdoor seating": 88,
    "Takeaway": 85,
    "Dine-in": 82,
    "Vegan options": 80,
    "Vegetarian options": 80,
    "Accepts reservations": 72,
    "Live music": 70,
    "Free Wi-Fi": 65,
    "Casual": 20,
    "Groups": 15,
    "Credit cards": 10,
}
```

A restaurant summary could be generated by:

1. Ranking groups for the category.
2. Ranking attributes within those groups.
3. Selecting no more than two attributes from one group during the first pass.
4. Filling remaining positions with the next-highest candidates.
5. Avoiding duplicate concepts.

The per-group limit prevents a summary containing only service options.

## 6. Normalization and deduplication

The source extraction should remain untouched, but the renderer should build a cleaned presentation layer.

For example, El Sol del Caribe currently shows `Credit cards` twice. That should render once.

Normalize values before presentation:

```python
def presentation_key(value):
    return normalize_whitespace(value).casefold()
```

Deduplicate within each group using that key.

Some attributes can be consolidated for display:

```text
Wi-Fi + Free Wi-Fi → Free Wi-Fi
Parking + Free parking → Free parking
```

This should use a conservative, version-controlled alias map:

```python
ATTRIBUTE_DISPLAY_ALIASES = {
    ("Wi-Fi", "Free Wi-Fi"): "Free Wi-Fi",
}
```

Do not automatically merge vaguely related concepts. For example:

- `Outdoor seating` and `Rooftop seating` are different.
- `Delivery` and `No-contact delivery` are different.
- `Accessible entrance` and `Accessible seating` are different.

Repeated values across different groups should be handled carefully. `Breakfast` under “Popular for” and “Dining options” reflects different Google contexts. In the collapsed summary, show it only once. In the expanded view, retaining both may be acceptable if the group context is useful.

## 7. Recommended markup

Use a native disclosure element where practical:

```html
<section class="business-details" aria-labelledby="details-heading">
  <div class="details-header">
    <h2 id="details-heading">Details</h2>
    <p class="details-source">
      From
      <a href="GOOGLE_MAPS_URL">Google Maps</a>
      · Captured August 2026
    </p>
  </div>

  <ul class="details-summary" aria-label="Highlighted details">
    <li>Wheelchair-accessible entrance</li>
    <li>Outdoor seating</li>
    <li>Dine-in</li>
    <li>Vegetarian options</li>
    <li>Accepts reservations</li>
    <li>Free Wi-Fi</li>
  </ul>

  <details class="details-disclosure">
    <summary>
      <span class="when-closed">View all 67 details</span>
      <span class="when-open">View fewer details</span>
    </summary>

    <div class="details-groups">
      <!-- Complete grouped attributes -->
    </div>
  </details>
</section>
```

There are two implementation choices:

### Summary outside the disclosure

Keep the highlighted attributes visible while the complete set opens beneath them.

Advantage: users retain the useful summary.

Risk: attributes may appear twice unless the expanded portion excludes summary items or visually indicates the full set.

### Summary replaced by expanded content

Hide the summary while the complete collection is open.

Advantage: no duplication.

This is the cleaner option:

```css
.details-disclosure[open] ~ .details-summary {
  display: none;
}
```

The exact DOM order can be arranged so the rule works naturally.

## 8. Expanded presentation style

Chips work well for a handful of scannable values. They become visually noisy in groups of sixty.

I would keep chips in the collapsed summary but use compact grouped lists in the expanded view:

```text
SERVICE OPTIONS
• Outdoor seating
• Delivery
• Takeaway
• Dine-in
```

On wider screens, each group can use two columns:

```css
.details-group-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.35rem 1rem;
}
```

On mobile, use one or two columns depending on available width and label length.

This provides a visual distinction:

- Summary: attractive, prominent chips
- Complete data: quieter, information-dense lists

If the existing design language strongly favors chips, they can remain in the expanded view, but should have reduced padding and lower contrast.

## 9. Mobile behavior

The mobile layout is the main reason to implement this design.

The collapsed section should occupy roughly one-third to one-half of a viewport—not several screens.

Target:

```text
DETAILS
From Google Maps

[Outdoor seating] [Dine-in]
[Vegan options] [Accessible entrance]
[Accepts reservations]

View all 67 details
```

The sticky Directions/Share bar must not cover the final rows or the “View fewer details” control. Add bottom padding equal to the sticky bar’s height plus a safe margin:

```css
.business-page {
  padding-bottom: calc(var(--action-bar-height) + 1.5rem);
}
```

Touch targets for the disclosure control should be at least approximately 44 pixels high.

## 10. List-card behavior

Do not add the full Details dataset to directory cards. That would transfer the same flooding problem to the search results.

At most, cards could eventually show two highly discriminating highlights:

```text
Outdoor seating · Vegan options
```

But I would initially keep list cards unchanged. Improve the dedicated business page first and measure whether visitors need more information before opening it.

## 11. Provenance

Place the provenance label directly under the Details heading:

```text
From Google Maps · Captured August 2026
```

“Google Maps” should link to the exact listing URL.

This label should be visually secondary but readable. Do not repeat it under every group.

Internally, retain:

```json
{
  "source": "google_about",
  "capturedAt": "2026-08-02T...",
  "googleCid": "...",
  "extractorVersion": "google-maps-about-attributes-v1"
}
```

The interface can format the precise timestamp as a month and year.

## 12. Empty and partial states

### No attributes

Omit the Details section entirely. Do not display:

```text
Details unavailable
```

Absence of extracted Google attributes is not useful to visitors.

### One or two attributes

Show them directly with no disclosure.

### Extraction incomplete or identity uncertain

Do not publish those attributes until reviewed. Preserve them in the enrichment output with their status.

### Closed businesses

Existing attributes may be stale. Either omit them or clearly retain the capture date while prioritizing the “Permanently closed” status.

## 13. Suggested implementation structure

Keep the original data and presentation transformation separate:

```python
raw_attributes = business["google_about_attributes"]

display_model = build_attribute_display_model(
    category=business["category"],
    groups=raw_attributes,
)
```

Return something like:

```json
{
  "totalCount": 67,
  "summary": [
    {
      "group": "Accessibility",
      "value": "Wheelchair-accessible entrance"
    },
    {
      "group": "Service options",
      "value": "Outdoor seating"
    }
  ],
  "expandedGroups": [
    {
      "name": "Accessibility",
      "attributes": ["..."]
    }
  ],
  "collapsedByDefault": true,
  "source": {
    "label": "Google Maps",
    "capturedAt": "2026-08-02",
    "url": "..."
  }
}
```

The template should only render this model. Ranking, deduplication, aliases, and thresholds belong in the model-building code—not scattered through HTML generation.

## 14. Rollout plan

Implement in stages:

1. Add presentation-layer deduplication.
2. Add the category and attribute priority configuration.
3. Build the summary model.
4. Add the master disclosure.
5. Add provenance.
6. Add mobile bottom spacing.
7. Test representative pages:
   - 67 attributes
   - 18 attributes
   - amenities plus attributes
   - fewer than 8 attributes
   - no attributes
8. Verify keyboard and screen-reader behavior.
9. Test at approximately 390px mobile width and normal desktop width.
10. Deploy without changing the underlying extracted dataset.

The desired result is not less data. It is a clearer hierarchy: immediately useful facts first, exhaustive evidence on demand.