# CID Enrichment Strategy Report

## How Maps Pages Vary by Business Type

Based on deep inspection of 11 businesses across 6 categories (hotel, hostel, restaurant, shopping, tour_company, services), each with full visible text capture, link analysis, and image metadata.

---

## 1. Hotels & Lodging (Black Bamboo, La Tica y La Gata)

**Page footprint:** 170-176 lines, ~3600 chars, 8 links, 24-25 images

**Rich data available:**
| Field | Present? | Notes |
|-------|----------|-------|
| Rating | Yes | Always present |
| Subcategory | Yes | "Bed & Breakfast", "Hotel" |
| Street address | Yes | Full descriptive address |
| Plus Code | Yes | M742+8M format |
| Phone | Yes | |
| Website | Yes | Direct business URL |
| Check-in / Check-out | Yes | Lodging-specific |
| Amenities list | Yes | Pool, WiFi, parking, AC, etc. |
| Booking prices | Yes | CRC amounts + competitor prices |
| Nearby competitors | Yes | Hotel names + ratings + prices |
| Vacation rental prices | Yes | Nearby rental listings with descriptions |
| Photo URLs | Yes | lh3.googleusercontent.com paths |
| Open/Closed status | No | Not shown for hotels |

**What v1 captured correctly:** Rating, subcategory, phone, website, plus code, check-in/out, amenities, prices, nearby competitors
**What v1 missed:** Street address (took Plus Code instead), photo URLs

---

## 2. Restaurants & Cafes (Gigi O, Tasty Waves, Pizzeria Pulcinella, Caribeans)

**Page footprint:** 69-82 lines, ~1400-2200 chars, 5 links, 4-6 images

**Rich data available:**
| Field | Present? | Notes |
|-------|----------|-------|
| Rating | Yes | Always |
| Subcategory | Yes | "Restaurante", "Cafeteria", "Restaurante italiano" |
| Street address | Yes | Sometimes short, sometimes full |
| Plus Code | Sometimes | Not always shown |
| Phone | Yes | |
| Website | Yes | Direct URL |
| **Open/Closed status** | **Yes** | **"Abierto" / "Cerrado" — NOT captured in v1** |
| **Hours of operation** | **Yes** | **"jueves 7:30 a.m. - 6 p.m." — NOT captured in v1** |
| Menu links | Sometimes | Not consistently shown |
| Photos | Yes | Fewer than hotels |
| Amenities | Yes | More generic than hotels |
| Prices | No | Menu prices NOT shown on Maps CID page |
| Check-in/out | No | Not relevant |
| Nearby competitors | No | Not shown in same way as hotels |

**What v1 captured correctly:** Rating, subcategory, phone, website, business name
**What v1 missed:** Open/closed status, hours of operation, street address, photo URLs
**Biggest loss:** Hours of operation (100% of food businesses have them, 0% captured)

---

## 3. Shops & Retail (Old Harbour Supermarket, Tienda Caribe)

**Page footprint:** 68-77 lines, ~1500 chars, 5-7 links, 4-5 images

**Rich data available:**
| Field | Present? | Notes |
|-------|----------|-------|
| Rating | Yes | |
| Subcategory | Yes | "Supermercado", "Tienda de ropa" |
| Street address | Sometimes | |
| Plus Code | No | Not shown consistently |
| Phone | Yes | |
| Website | Sometimes | Many shops don't have websites |
| **Open/Closed status** | **Yes** | **"Abierto" / "Cerrado"** |
| Hours of operation | Sometimes | Less consistently than restaurants |
| Photos | Yes | Few |
| Amenities | Yes | Generic (parking, transport) |

**What v1 captured:** Rating, phone, subcategory
**What v1 missed:** Open/closed status, street address, hours

---

## 4. Tour Companies & Attractions (Jaguar Rescue Center)

**Page footprint:** ~70 lines, ~1600 chars, 5 links, 4 images

| Field | Present? |
|-------|----------|
| Rating | Yes |
| Subcategory | Yes ("Servicio de rehabilitacion de la fauna") |
| Street address | Yes (descriptive) |
| Phone | Yes |
| Website | Yes |
| Open/Closed | No |
| Hours | No |
| Photos | Yes |
| Prices | No |

**Similar to restaurants** in structure but no hours/status shown. Website and phone are the most valuable.

---

## 5. Services (Black Shack Surf School, Lavanderia La Estrella)

**Page footprint:** 48-67 lines, ~1100-1500 chars, 2-3 links, 3-4 images

**Significantly sparser.** Many services show only:
- Rating (sometimes)
- Phone (sometimes)
- Subcategory
- Generic amenities (transport, parking)
- No website
- No street address
- No hours

**Note:** Black Shack Surf School returned only 48 lines and showed "Instrucciones sobre como llegar" as the business name — Maps served a reduced page, likely due to logged-out viewport limits or data quality issues.

**This is the category where re-scanning with an authenticated Chrome profile would make the biggest difference.**

---

## 6. Hostels (Rocking J's Hostel)

**Page footprint:** 48 lines, ~1100 chars, 2 links, 4 images

Same problem as services — very sparse data. Only generic amenities captured. No phone, no rating, no website visible.

**Likely cause:** Maps serves a limited view for some businesses when not logged in. Some businesses may have incomplete Google Maps profiles.

---

## Cross-Category Field Matrix

| Field | Hotel | Restaurant | Shop | Tour | Service | Hostel |
|-------|:-----:|:----------:|:----:|:----:|:-------:|:------:|
| Rating | 100% | 100% | 100% | 100% | 50% | 0% |
| Subcategory | 100% | 100% | 100% | 100% | 50% | 0% |
| Phone | 100% | 100% | 100% | 100% | 50% | 0% |
| Website | 100% | 100% | 50% | 100% | 0% | 0% |
| Street Address | 100% | 67% | 50% | 100% | 0% | 0% |
| Plus Code | 100% | 33% | 0% | 0% | 50% | 0% |
| Open/Closed | 0% | 100% | 100% | 0% | 50% | 0% |
| Hours of Operation | 0% | 100% | 50% | 0% | 0% | 0% |
| Check-in/out | 100% | 0% | 0% | 0% | 0% | 0% |
| Amenities | 100% | 100% | 100% | 100% | 100% | 100% |
| Prices | 100% | 0% | 0% | 0% | 0% | 0% |
| Photo URLs | 100% | 100% | 100% | 100% | 100% | 100% |

---

## v2 Re-Scan Recommendations

### 1. Category-Aware Parsing

Do not use one parser for all. Instead:

```python
extractors = {
    "hotel": hotel_extractor,       # check-in/out, amenities, prices
    "restaurant": restaurant_extractor,  # hours, open/closed, cuisine
    "shopping": shop_extractor,     # hours, open/closed
    "tour_company": tour_extractor, # phone, website, address
    "services": service_extractor,  # basic: rating, phone, hours
    "hostel": hotel_extractor,      # same as hotel schema
}
```

### 2. Save Raw Text Always

Every CID scrape should save the complete visible text as a JSON field. This enables:
- Re-parsing when we discover new field patterns
- Auditing extraction quality
- Training better parsers

**Storage cost:** ~4KB per business x 699 = ~2.8MB. Negligible.

### 3. Authenticated Browser Profile

Some businesses (Rocking J's, Black Shack Surf School) returned <50 lines of data with a logged-out browser. Maps serves a drastically reduced page for some entities. Using a persistent Chrome profile with a logged-in Google account would likely unlock:
- Full business descriptions
- More photos
- Complete hours
- Phone and website for services/hostels

### 4. Capture Additional Fields

| Field | Priority | Effort | Impact |
|-------|:--------:|:------:|:------:|
| Street address (descriptive) | High | Low | High — currently missing from 5/11 samples |
| Open/Closed status | High | Low | High — real-time utility for visitors |
| Hours of operation | High | Low | High — essential for restaurants/shops |
| Photo URLs | Medium | Low | Medium — could power business page visuals |
| Full text save | High | None | Critical — enables future re-parsing |
| Links with labels | Medium | Low | Medium — menu links, booking links |

### 5. Implementation Strategy

**Phase A (no re-scan, do now):**
- Extract street address from existing text samples (limited by 300-char truncation)
- Add open/closed and hours parsing to the extractor for the overnight re-scan

**Phase B (overnight re-scan):**
- Re-run all 699 CIDs with v2 capture script
- Save full visible text
- Extract all known fields per category
- Store raw text for future parsing
- Use authenticated Chrome profile if available

**Phase C (post-analysis):**
- Analyze the full 699-text corpus for any remaining patterns
- Generate category-specific schemas
- Integrate new fields into the app display
