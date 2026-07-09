# Paradisio — Status & Idea Landscape

## Built

| Feature | Status | Detail |
|---------|--------|--------|
| Static app generator | Done | `build.py` — pure Python, reads CSV, outputs HTML/JSON |
| 750 business pages | Done | Full detail pages with contact routing |
| Search + filters | Done | Category, area, text, contact-channel filters |
| Pagination | Done | 50 at a time, load more, resets on filter change |
| Maps (Leaflet/OSM) | Done | Interactive pins on 606 business pages |
| Mobile-first CSS | Done | 4 viewports, sticky CTA bar, safe-area padding |
| Display name cleanup | Done | 380+ location suffixes stripped |
| QR generator | Done | 750 print-ready PNGs + redirect pages + gallery |
| QR on business pages | Done | Preview image + download link per business |
| Maps enrichment crawl | Done | 699 CIDs scanned — 640 ratings, 544 phones, 414 websites, 203 check-in/out, 215 amenities, 105 addresses |
| Ratings on biz pages | Done | Star ratings displayed on 640 pages |
| Amenities on biz pages | Done | Filtered, deduplicated chips on 215 pages |
| Addresses on biz pages | Done | Maps address on 105 pages |
| Hours on biz pages | Done | Check-in/out on 203 pages |
| GitHub Pages | Live | https://skinnerboxentertainment.github.io/mekatelyu/paradisio_app/ |

## Coverage (from the data)

| Channel | Count | % of 750 |
|---------|------:|:--------:|
| Google Maps CID | 699 | 93% |
| WhatsApp | 614 | 82% |
| Phone | 611 | 81% |
| Instagram | 452 | 60% |
| Instagram (verified) | 223 | 30% |
| Facebook | 361 | 48% |
| Website | 191 | 25% |
| Booking.com | 171 | 23% |
| Email | 75 | 10% |
| Coordinates | 606 | 81% |
| **Rating (Maps enrich)** | **640** | **85%** |
| **Amenities (Maps enrich)** | **215** | **29%** |
| **Check-in/out (Maps enrich)** | **203** | **27%** |
| **Address (Maps enrich)** | **105** | **14%** |

## Remaining Ideas

| # | Idea | What's needed |
|---|------|--------------|
| 2 | Premium listings ($100/$200) | Payments (SINPE), analytics, featured placement logic |
| 3 | QR affiliate network | Affiliate tracking, commission payouts, sales materials |
| 4 | AI service upsells (WhatsApp auto-reply, IG content pack, menu translation) | OpenAI integration per service |
| 5 | Middleman fees (10-20% on transport, tours, dining) | Concierge ops, dispute handling |
| 6 | Instagram capture engine (event detection, dashboards) | Scraping pipeline + analytics backend |
| 7 | Quarterly print magazine | Layout, print vendor, distribution |
| 8 | Creative layer (artists, musicians, photographers) | Profile type expansion, curation |
| 9 | Community layer (Reddit, Discord, blog) | Seeding, moderation, content ops |
| 10 | Town API (intent router for Puerto Viejo) | Query wrapper around existing JSON data |
| 11 | WhatsApp concierge (traveler-facing assistant) | WhatsApp Business API or web launcher |
| 12 | Refreshable scanner (port to other towns) | Run proven method on a second town |
| 13 | Craigslist classifieds (rooms, jobs, gigs, for sale) | Data model + rendering (same pattern as directory) |
| 14 | Puerto Viejo Economic Tarot (data-art oracle) | Static microsite with archetype cards |

## The Flywheel

```
Instagram posts → aggregated analytics & event detection
  → magazine editorial + real-time web app updates
    → physical distribution + QR code scans
      → tourist uses platform
        → business gets booked
          → business upgrades to premium
            → more Instagram posts
```

---

*Generated 2026-07-09*
