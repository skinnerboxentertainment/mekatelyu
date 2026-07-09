# CID Scan Post-Mortem

## How it worked

Playwright opened each `https://www.google.com/maps?cid={CID}` URL, waited for JS rendering, then extracted **all visible text** via DOM TreeWalker (skipping hidden elements). We did NOT capture the full HTML source — only the rendered text.

The extracted text was parsed for specific patterns. A 300-char sample was saved alongside the parsed fields. The full visible text was **discarded after parsing**.

## What we captured (11 fields across 674 businesses)

| Field | Example | Quality |
|-------|---------|---------|
| Rating | 4.7 | Good |
| Subcategory | Bed & Breakfast, Restaurante italiano | Good |
| Phone | 8417 5543 | Good |
| Website | blackbamboobb.com | Fair — sometimes grabs "Booking.com" or "facebook.com" |
| Plus Code | M742+8M Puerto Viejo | Good |
| Check-in | 3:00 p.m. | Good (hotels/lodging) |
| Check-out | 11:00 a.m. | Good (hotels/lodging) |
| Amenities | Wi-Fi, parking, pool, AC | Good |
| Prices | CRC 51,422 per night | Good — includes competitor prices |
| Review count | 264 | Fair — grabbed from nearby business list |
| Nearby businesses | Hotel Indalo (4.6, 0.3km) | Good |

## What's in the visible text that we DIDN'T extract

### 1. Full street address — HIGH VALUE, EASY FIX
Line 42 of Black Bamboo's visible text:
> `Camino de la Bakery 600m suroeste (hay que avanzar 400m mas a partir de la ubicacion, Limon, Puerto Viejo de Talamanca, 70403`

Our parser grabs the Plus Code (M742+8M...) but misses the full Spanish street address that appears on the line before it. **This is a parsing priority bug** — the address is there, we just check for the wrong pattern first.

### 2. Daily hours of operation (for restaurants/shops)
The visible text for some businesses shows hours like `Lunes: 8:00 - 22:00` but our parser only extracts check-in/check-out (lodging-specific). For restaurants, cafes, shops, the actual open/close hours are on the page but not extracted.

### 3. Menu links (restaurants)
For restaurants, Maps shows a "Menu" section with links. These appear in the visible text but aren't extracted.

### 4. Specific business type with more granularity
The subcategory "Restaurante italiano" > "Restaurante" tells us more than our current category field of "restaurant". We've added extraction for this but it only works well when the text sample didn't get truncated.

### 5. Photo URLs
The HTML source contains image URLs (`lh3.googleusercontent.com/gps-cs-s/...`). We don't capture these since we only extract text. These could be used as business photos with proper attribution/terms.

## What's NOT available on the Maps page at all

- No JSON-LD structured data
- No meta tags specific to the business (all generic Google Maps metadata)
- No full business description text (Maps doesn't show one on the CID page)
- No actual review text (only buttons to write reviews)
- No social media links embedded in the page
- No email addresses

## What requires a re-scan to capture

Since we discarded the full visible text after parsing, these require re-running the CID crawl:

1. Daily hours of operation for non-lodging businesses
2. Menu links for restaurants
3. Full street address text (easy parser fix, but would need re-scan since we didn't save full text)
4. Photo URLs (require capturing HTML, not just text)

## Recommendation

**Low-hanging fruit (no re-scan needed):**
- The subcategory field has already been extracted from the existing text samples and is now displaying on business pages
- The existing 300-char text samples (~674 of them) could be re-parsed for street addresses and hours, though the truncation makes this unreliable

**Medium effort (re-scan needed for clean data):**
- Re-run the CID crawl with a broader parser that captures: street address, daily hours, menu links
- Save the full visible text this time as a JSON field for future re-parsing
- This would take ~3 hours (same as first pass) with pacing

**High effort (full HTML capture):**
- Capture the full innerHTML of the Maps page for each CID
- Extract image URLs, hidden metadata, and any JS-injected data
- Much larger storage (176KB per page × 699 = ~120MB)
- Legal considerations around image use
