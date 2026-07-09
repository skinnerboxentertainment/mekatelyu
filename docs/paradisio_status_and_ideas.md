# Paradisio — Status & Idea Landscape

## Current Build State (what exists now)

### The App — `docs/paradisio_app/`
A persistent, static web directory of **750 businesses** within 5 km of Puerto Viejo de Talamanca, Costa Rica. Generated from `pv_master_unified.csv` in one Python pass.

| Layer | Tech | Notes |
|-------|------|-------|
| Generator | `paradisio_app/build.py` | Pure Python stdlib, reads CSV, outputs static HTML/JSON |
| Frontend | Vanilla HTML/CSS/JS | No frameworks, no build step, no dependencies |
| Search | Client-side JS over `businesses.json` | Category, area, text, contact-channel filters |
| Pagination | Load More (50 per page) | 750 results don't kill the DOM; resets on filter |
| Maps | Leaflet.js + OpenStreetMap | Interactive pin on each business page (606 with coords) |
| Mobile | CSS with 4 viewport breakpoints | 2-column filter grid, sticky bottom CTA bar, safe-area padding |
| Hosting | GitHub Pages via `docs/` | Zero infra, zero cost |
| Capture | `capture_mobile.py` | Playwright script, 16 screenshots across 4 viewports |
| Design | Verified by Codex visual review | Two rounds of critique applied, verdict: shippable |

### Coverage (from the data)

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

### Every Business Page Has
- Name (cleaned — location suffixes stripped)
- Category + area + operating status
- Primary contact CTA (WhatsApp > call > Instagram > website > map)
- Secondary links (all available channels)
- Interactive OpenStreetMap (if coordinates exist)
- Score bars (Contactability, Visibility, Completeness)
- Badges (WhatsApp, Instagram, Booking, Map Verified, etc.)
- "Claim this page" CTA (mailto link for v1)
- Sticky bottom action bar on mobile

---

## The Full Idea Landscape

These are the ideas that came out of the brainstorming sessions with you and Codex. They range from immediate action to long-term moonshots. They are not ranked — they are presented as a menu.

---

### Idea 1: The Opt-Out Listing (already built)

**Thesis:** Every business is on the board by default. They don't opt in — they opt out. This flips the standard directory model: instead of convincing 12 businesses to join, 750 are already live. The friction moves from "convince them to sign up" to "make the listing good enough they don't want to leave."

**Status:** Built. 750 businesses live at `docs/paradisio_app/`. The board exists.

---

### Idea 2: Premium Listings ($100 / $200)

**Thesis:** Year 1, a business pays $100 to own their page, get a QR sticker, see analytics. Year 2 renews at $200. The $100 isn't revenue — it's a commitment mechanism. By year 2, the platform is generating enough inbound that $200 is cheaper than any alternative.

**What they get:**
- Permanent page with their photos, contact channels, map pin
- Physical QR code sticker for their door/window (SINPE trackable)
- Featured placement in their category and neighborhood
- Monthly scan/view analytics
- Auto-generated business page from their existing data

**Status:** Not built. Requires: payment processing (SINPE/BTC), analytics backend, QR generator.

---

### Idea 3: QR Code Affiliate Network

**Thesis:** Local salespeople (students, surf instructors, bartenders, ticos) walk the town selling QR code stickers. They know the business owners. They close in person with cash or SINPE. Commission is paid instantly.

**Pitch:**
> *"Your restaurant is already on the Puerto Viejo board. 50 people saw your page this month. Put this QR code on your door and every tourist Instagramming their food can message you directly. First year, we do the sticker and setup — 10 mil colones."*

**QR tiers:**

| Variant | Price |
|---------|-------|
| Basic — opens listing page + WhatsApp | $100/yr |
| Menu — opens menu + WhatsApp | $150/yr |
| Booking — opens Booking/Airbnb + WhatsApp | $200/yr |
| Review — opens TripAdvisor/Google review | $50/yr add-on |

**Status:** Not built. Requires: QR generation, affiliate tracking, payment processing.

---

### Idea 4: AI Service Upsells ($10-30/mo)

**Thesis:** The dataset already knows everything about each business. AI can augment their digital presence for a fraction of what a website costs.

| Service | What AI does | Price |
|---------|-------------|-------|
| WhatsApp auto-reply | AI answers common questions (hours, menu, prices, location) in Spanish/English | $20/mo |
| IG content pack | 4 AI-generated posts/month from their business data | $30/mo |
| Menu/price translation | Spanish/English/French translation of menu or service list | $50 one-time |
| Review response drafts | Auto-generate replies to TripAdvisor/Google reviews | $15/mo |
| Booking link integration | Connect Booking.com/Airbnb calendar to their page | $10/mo |
| Photo refresh | AI-enhanced or commissioned photography of their space | $75 one-time |

**Status:** Not built. Requires: OpenAI API integration, service delivery automation.

---

### Idea 5: Middleman Service Fees (10-20%)

**Thesis:** Don't just list businesses — intermediate transactions. When a tourist books a van driver, a tour, or a table, the platform handles the confirmation, the bilingual coordination, the reminders, and the fallback. Take 10-20% for being the trusted referrer.

| Category | Your cut |
|----------|:--------:|
| Transport (shuttle, van SJ↔PV, taxi, boat) | 10-15% |
| Tours (snorkeling, sloth, chocolate, night walk) | 10-20% |
| Dining (reservation with pre-order) | 5-10% |
| Activities (surf lessons, yoga, bike rental) | 10-15% |
| Services (massage, laundry, bike repair) | 15-20% |

**Key insight:** You don't need a booking engine. The transaction happens on WhatsApp + SINPE. You confirm both sides, take your cut. The platform is a coordination layer, not a payment processor.

**Status:** Not built. Requires: concierge workflow, dispute handling, human ops for v1.

---

### Idea 6: Instagram Capture Engine

**Thesis:** 452 verified Instagram handles. Every post, story, and hashtag from every business in town is captured continuously. This feeds:

| Output | What it does |
|--------|-------------|
| Event detection | 3 hotels IG'd the same thing = there's a festival, wedding, retreat |
| Dinner rush signal | Restaurants posting specials in real time |
| Surf/beach report | Surf schools posting wave pics |
| Dead zone detection | Areas with no posts this week = invisible businesses |
| Hashtag analytics | #PuertoViejo, #Cocles, #Cahuita trending over time |
| Magazine content | Aggregated IG data becomes editorial |

**Business-facing dashboard:**
- Your post reach this month
- Your hashtag performance vs. competitors
- Best times to post by category
- "You're the most Instagrammed coffee shop in Cocles"

**Status:** Not built. Requires: Instagram API/scraping pipeline, analytics backend.

---

### Idea 7: Quarterly Print Magazine

**Thesis:** A beautiful, high-gloss, bilingual printed magazine distributed to every hotel lobby, hostel common room, rental villa, tour desk, and bar in town. It's not content marketing — it's evidence of belonging.

**Content sourced from the data stream:**
- "The 20 Most Instagrammed Tables in Puerto Viejo This Season"
- "What Cocles Ate in July" — aggregated from restaurant Instagrams
- "Wave Report" — surf spots ranked by IG story frequency
- "The Quiet Places" — businesses with amazing service but zero social presence
- "New in Town" — detected from new Instagram accounts
- Full-page premium member ads
- QR code on every page → deep link to the business on the platform

**Why businesses host it:** It makes their lobby feel curated. They don't realize they're also distributing a sales catalog that trains every tourist to use the platform. FOMO is built in: businesses that didn't pay see their name next to ones that did.

**Status:** Not built. Requires: layout/design, print vendor, distribution network.

---

### Idea 8: The Creative Layer

**Thesis:** The platform isn't just hotels and restaurants. It's also the people who make the town feel alive: photographers, musicians, poets, muralists, surf instructors, chefs as artists, models, content creators, international collaborators. They get profiles alongside the businesses.

**Why it matters:** The creative layer is the content engine that makes the business board *interesting.* A tourist doesn't just look for a hotel — they look for what's happening tonight. The artists posting their gigs, the photographer offering a sunset shoot, the poet doing a reading at the hostel bar — this is what makes a town feel alive.

**Cross-listing:** *"You're a bar. Your musician plays here every Thursday. We cross-list them. Their fans find you, your guests find them."*

**Status:** Not built. Requires: profile type expansion, curation, community management.

---

### Idea 9: The Community Layer

**Thesis:** A set of surfaces where the town's pulse lives — all fed by the same data stream.

| Surface | Purpose |
|---------|---------|
| Reddit (r/PuertoViejo) | Visitor questions, trip reports, "is this place still good?" |
| Discord | Real-time chat: live music tonight, surf conditions, rideshares |
| Blog | Long-form profiles, deep interviews, photo essays, history |
| Magazine | Quarterly print version of the best content |

**Status:** Not built. Requires: community seeding, moderation, content operations.

---

### Idea 10: The Town API

**Thesis:** Puerto Viejo as a programmable place. An intent router that answers questions no global platform optimizes for:

| Endpoint | What it does |
|----------|-------------|
| `/places/search` | "vegan lunch near Cocles with Instagram and WhatsApp" |
| `/places/nearby` | Lodging dense area filtered for laundry, pharmacy, breakfast |
| `/itinerary/blocks` | 3-hour, half-day, rainy-day, no-car, surf-adjacent routes |
| `/business/{id}/contact` | Normalized phone, WhatsApp deep link, IG, FB, Booking, TA |
| `/market/gaps` | "Areas with 20+ lodging and fewer than 3 restaurants" |
| `/visibility/score` | Completeness/findability score for each business |
| `/changes` | New, closed, renamed, newly social, lost coordinates |

**Status:** Not built. The data exists and is normalized. Building the API is a matter of wrapping the existing JSON with query logic.

---

### Idea 11: WhatsApp-Native Concierge

**Thesis:** A traveler messages one number. The concierge replies with 3 options, each with a WhatsApp deep link, a Spanish prefilled message, and a map link. The core product is not an AI travel planner — it is a contact bridge. It shortens the distance between visitor intent and local business conversation.

**Key product decisions:**
- Bilingual by default
- Generates prefilled WhatsApp messages in Spanish
- Falls back through contact channels intelligently
- Has modes: near me, open now, low friction, local/less touristy, rain plan, no car, family
- Can be embedded by hotels (QR card at reception)
- Ends at the threshold of human conversation — deliberately does not complete bookings

**Status:** Not built. Requires: WhatsApp Business API or web-based launcher, query engine over the CSV.

---

### Idea 12: Refreshable Town Scanner (the portable machine)

**Thesis:** The weekend pipeline that produced Puerto Viejo is more valuable than the dataset itself. Package it as a replicable zero-API-cost "town scanner" for other tourism towns.

**Output package:**
- Master CSV / SQLite / API of businesses within a radius
- Confidence + provenance per field
- Coverage report: Maps, OSM, local directories, websites, Instagram
- Gap report: missing coordinates, missing categories, no phone, no social
- Change report on refresh: new, gone, renamed, contact changed
- Opportunity map: service gaps, digital presence gaps, lodging/restaurant imbalance

**Target customers:** DMOs, boutique hotel groups, travel media, local SEO agencies, relocation guides, market researchers, entrepreneurs scoping new locations.

**Status:** Not built. The method exists (proven on Puerto Viejo). Needs to be productized and tested on a second town.

---

### Idea 13: Craigslist for Puerto Viejo (Classifieds Board)

**Thesis:** A Craigslist-style classifieds board alongside the business directory. Rooms for rent, surfboards for sale, gigs, jobs, lost & found, rideshares, community events, language exchange, yoga meetups, tour guides offering off days. Anyone can post — no account needed, just an email or phone.

**Why it fits:**
- The directory already has the town's commercial skeleton. The classifieds add the town's living tissue — the daily exchange that makes a place functional.
- Craigslist's power was never the tech. It was that the whole community used it. We already have 750 businesses opted in. The network effect is seeded.
- Same aesthetic: text-first, fast, no JavaScript needed to read, works on a $30 phone.

**Integration with the existing system:**
- Business owners who pay for premium also get a free classifieds section for their job openings, room rentals, equipment sales
- QR codes on business pages could link to their classifieds
- The post ad workflow is a mailto: (like the claim workflow) — v1 is human-mediated

**Monetization:** Featured classifieds for a small fee ($5-10). Job listings from premium businesses are free. Everything else is free for now.

**Status:** Not built. Data model and rendering would mirror the directory pattern (static pages from a JSON feed).

---

### Idea 14: Puerto Viejo Economic Tarot

**Thesis:** A playful, eerie, data-driven artifact. A visitor draws three cards — Past, Present, Future — each representing a business archetype from the dataset. The reading generates a walk, a meal, a conversation prompt, and a micro-economic observation about the town.

**Archetypes derived from the CSV:**
- The Ghost: business visible in one source but absent elsewhere
- The Beacon: complete digital presence
- The Whisper: no website, maybe phone only
- The Portal: WhatsApp-ready business
- The Mask: tourist-facing brand with little local metadata
- The Root: services locals need, not just visitors
- The Tide: lodging cluster pulling restaurants/shops around it

**Could become:**
- A weird travel guide
- A data-art website
- A deck of physical cards sold locally
- A daily "town reading" on Instagram
- A walking-tour generator
- A way to make invisible local commerce emotionally legible

**Status:** Not built. The data exists and archetypes are definable. Cheapest MVP is a static microsite.

---

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

## This Build Session (today)

| What | Status |
|------|--------|
| CODEX_ENDPOINT v2 migrated from devChorus | Done |
| Paradisio Vision doc written | Done |
| Paradisio Build Spec written | Done |
| Static app generator built | Done |
| 750 business pages generated | Done |
| Client-side search, filters, pagination | Done |
| Interactive maps (Leaflet) | Done |
| Mobile-first CSS (4 viewport sizes) | Done |
| Playwright capture script | Done |
| Codex visual review (2 rounds) | Done |
| Display name cleanup (380+ names) | Done |
| Git repo with mekatelyu remote | Remote exists, push pending |

---

*Generated 2026-07-09*
