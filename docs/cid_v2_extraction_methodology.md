# CID v2 Extraction Methodology

## v1 Failure Mode

The first CID pass was **parser-first**: we designed extraction rules for hotels (rating, phone, website, check-in/out, amenities, prices), ran them against 699 CIDs, and discarded the raw text. This meant:

- Restaurant pages with daily hours but no check-in/out → missed
- Shop pages with street addresses but no Plus Code pattern → missed
- Tour company pages with no amenities → empty
- Any data we didn't know to look for → permanently lost

## v2 Methodology: Capture-Then-Parse

### Principle
**Save everything during capture. Parse later, iteratively.**

The Maps page for a hotel vs a restaurant vs a surf shop exposes different fields. We cannot design one schema upfront. Instead:

### Capture Phase (what we save per CID)

| Field | Type | Why |
|-------|------|-----|
| `cid` | string | Identifier |
| `business_name` | string | From our dataset |
| `category` | string | From our dataset |
| `full_text` | string | **All visible text** (was 300-char sample) |
| `text_length` | int | Length for reference |
| `links` | array | All anchor hrefs with text labels |
| `images` | array | All img src URLs with alt text |
| `jsonld` | array | Any structured data found |
| `title` | string | Page title |
| `screenshot_path` | string | Reference screenshot |
| `captured_at` | timestamp | When captured |

Nothing is parsed during capture. The full text is preserved.

### Analysis Phase (post-capture)

Group captured businesses by category (hotel, restaurant, shop, tour, service, etc.) and identify which fields appear consistently within each group. For example:

**Hotels consistently show:**
- Rating, price range, amenities list, check-in/out, nearby competitors

**Restaurants/Cafes consistently show:**
- Rating, hours of operation, open/closed status, street address, website, photos

**Shops consistently show:**
- Rating, hours, street address, phone, website

**Tour companies consistently show:**
- Rating, phone, website, photos, review count

**Services (massage, laundry, etc.) consistently show:**
- Rating, phone, hours, street address

### Schema Generation Phase

For each category group, define:
- Required fields (must extract)
- Optional fields (extract if present)
- Category-specific fields (e.g., hours for restaurants, amenities for hotels)

### Extraction Phase

Write category-aware parsers that use the schema to extract the right fields per business type. Run against the saved full_text corpus (no re-crawl needed).

### Benefits
- No data loss — full text is preserved for future re-parsing
- Schema evolves iteratively — add new fields without re-crawling
- Category-specific — hotel parser doesn't miss restaurant data
- Audit trail — raw text is available for debugging extraction bugs
