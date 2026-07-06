# Independent Review: Enrichment Strategy

**Date:** 2026-07-06  
**Scope:** Desk review from existing project files and general platform knowledge. Per request, I did **not** execute scrapes, browser searches, live web searches, or third-party lookups.

## Executive take

The strategy is directionally good, but it overestimates the value and safety of several "low risk" phases. The strongest work is still local cache mining, OSM tag extraction, real website crawling, and direct Maps CID page extraction for known CIDs. The weakest parts are bulk Instagram probing, Facebook search, Airbnb scraping, WhatsApp verification assumptions, and the belief that visual scraper free tiers meaningfully offload Google risk.

The biggest issue is sequencing: the 134 grid-only records are currently barely usable because they lack coordinates and CIDs. Social enrichment on already-mapped records is less urgent than turning those 134 names into geospatial records. If zero Google Search risk is a hard constraint, accept that those records will remain low-confidence until a different source provides coordinates.

Recommended posture:

1. Do all local/offline extraction first.
2. Crawl real business websites second.
3. Extract known-CID Maps pages before speculative social scraping.
4. Use OTA/platform searches only for lodging/tour/restaurant classes where they are likely to exist.
5. Treat Google Search, Instagram, Facebook, WhatsApp, Airbnb, and TikTok as rate-limited, account/IP-sensitive work, not "low risk" bulk jobs.
6. Do not pay for or depend on Octoparse/ParseHub-style tools unless a small pilot proves output quality and export limits.

## 1. Affiliate and booking platforms missed

### Lodging and vacation rentals

Relevant beyond Booking/Airbnb:

- **Hostelworld**: high value for the 17 hostel records plus budget accommodations. Better signal than Airbnb for named hostels.
- **Expedia / Hotels.com / Vrbo**: Expedia Group properties often cross-list. Vrbo is useful for villas and vacation rentals, less useful for small hotels.
- **Agoda**: relevant for international travelers; can have independent hotel inventory not obvious on Booking.com.
- **Trip.com**: lower priority, but sometimes mirrors hotel inventory.
- **Google Hotels / hotel booking modules**: useful as a reference if already on a Maps page, but scraping search surfaces carries Google risk.
- **Trivago / Kayak / Skyscanner hotels**: mostly metasearch. Useful for discovering OTA URLs, not usually a primary source of business contact data.
- **Priceline**: lower priority in Costa Rica compared with Booking/Expedia ecosystems.
- **Hostelz**: niche hostel directory; lower volume but useful for hostel cross-checks.
- **Couchsurfing**: likely low value for commercial directory enrichment. It is account-based, community/member-oriented, and not a clean business listing source.
- **FlipKey**: historically TripAdvisor vacation rental inventory. Lower priority now; may produce stale or duplicate listings.

Costa Rica / regional lodging sources worth considering:

- **Visit Costa Rica / ICT ecosystem**: official tourism authority material can validate formal operators, but coverage may skew toward registered tourism businesses.
- **Small local tourism directories and area guides**: useful for named businesses, but quality is uneven and many pages are stale. These are best treated as evidence sources, not canonical data.
- **Puerto Viejo / Caribe Sur local directories**: the existing PVS source already covers much of this niche. Other local directories may add tours, restaurants, wellness, surf schools, and transport businesses, but require duplicate handling.

### Tours and activities

High-value platforms:

- **Viator**: likely the highest-value tour affiliate source. Good for tour companies, transport, activities, and day trips.
- **GetYourGuide**: useful but may have fewer local operators than Viator.
- **TripAdvisor Experiences**: often overlaps with Viator, but still useful for reviews and product names.
- **Airbnb Experiences**: possible but lower confidence; availability and public discoverability vary.
- **Klook**: lower priority for Puerto Viejo, but worth a small targeted check for tours/transport.

Tour-specific caution: many platform listings are product listings, not business profiles. A Viator page may represent a reseller or operator name that does not exactly match the local business.

### Restaurants and food delivery

Likely sources:

- **Uber Eats**: possible in Costa Rica, but Puerto Viejo coverage may be limited compared with San Jose. Also dynamic and location-dependent.
- **PedidosYa**: common in Latin America, potentially relevant in Costa Rica. Worth checking as a platform category, but local Caribbean coverage may be thin.
- **Restaurant Guru / Menulist / Wanderlog / HappyCow**: useful for restaurants, vegan/vegetarian places, cafes, and bars. These are not booking platforms, but can expose websites, phones, and social links.
- **OpenTable**: low expected value for Puerto Viejo.
- **TheFork**: low expected value for Costa Rica/Puerto Viejo.

### What I would add to the schema

Instead of one field per platform forever, consider these columns:

- `platform_urls`: JSON object or semicolon list keyed by platform.
- `platform_review_count`: optional per-platform structured field if analysis needs it.
- `source_evidence`: compact provenance field for how a URL was found.

This avoids schema sprawl as platforms are added.

## 2. Free/cheap scraping tools

### Octoparse

Useful for non-engineers and for quick proof-of-concept extraction. It has templates for common sites, including Google Maps in many marketing materials. However, the practical constraints are usually export limits, cloud-run limits, anti-bot breakage, and upsell to paid plans. It does not magically remove ToS or data quality risk. If it uses local execution, your IP can still be exposed. If it uses cloud execution, quality depends on their proxy/browser infrastructure.

Verdict: worth a tiny pilot only. Do not build the strategy around it.

### ParseHub

Similar story: visual scraping is convenient for semi-structured pages, but modern sites like Booking, Airbnb, Google Maps, Facebook, Instagram, and TikTok are JS-heavy and aggressively defended. Free tiers tend to be constrained by project/page limits and speed. Debugging selectors can cost more time than writing a focused scraper.

Verdict: useful for simple local tourism directories, not reliable as the main engine for Google/Booking/Airbnb.

### Scrapy Cloud / Zyte

Better fit for engineered crawling than visual tools. Scrapy is excellent for static or moderately dynamic websites and local directories. For Google Maps, Airbnb, Instagram, Facebook, and WhatsApp, it is not a magic bypass. Zyte's paid scraping/browser/proxy services may help, but that violates the "free/no paid APIs" spirit if used beyond free tier.

Verdict: strong for websites/directories; weak for account-guarded or bot-hostile platforms unless paid services are introduced.

### Other tools to consider

- **Apify**: many ready-made actors for Google Maps, Booking, Airbnb, Instagram, TripAdvisor. Often useful, but free credits are limited and production use becomes paid quickly.
- **Instant Data Scraper / browser extensions**: useful for manual extraction from simple tables/search results. Not robust for the key hard targets.
- **Playwright scripts**: best match for this repo because the existing workflow already uses Playwright and persistent browser profiles.
- **Scrapy + httpx + BeautifulSoup**: best for business websites, local directories, and OSM-like structured sources.

Bottom line: most free-tier tools are not pure bait-and-switch, but for this exact workload they are mostly evaluation tools. The durable path is custom scripts plus strict pacing and provenance.

## 3. Instagram handle guessing at scale

The current proposed patterns are too narrow. For Puerto Viejo / Costa Rica, handles commonly include:

- Business name compressed: `blackbamboo`
- Business name with underscores: `black_bamboo`
- Business name with dots: `black.bamboo`
- Location suffixes: `_pv`, `pv`, `_puertoviejo`, `puertoviejo`, `_cr`, `cr`, `_costarica`, `costarica`
- Beach/town suffixes: `cocles`, `playanegra`, `puntauva`, `manzanillo`, `caribesur`
- Category words: `hotel`, `hostel`, `restaurant`, `cafe`, `soda`, `tours`, `surf`, `yoga`, `spa`
- Spanish variants: `restaurante`, `cabinas`, `sodas`, `alquileres`, `tours`
- Abbreviations/initialisms for long names.

Optimal strategy:

1. Normalize name: lowercase, strip accents, remove legal/category filler words, remove punctuation.
2. Generate a limited candidate set, not 20+ guesses per record. Start with 5-8 high-probability candidates.
3. Score candidates before requesting Instagram:
   - exact compressed name
   - exact underscore/dot form
   - name + `pv`
   - name + `cr`
   - name + `puertoviejo`
   - name + area if known
4. Verify profile existence and then verify identity. A 200 profile is not enough. Bio/name/location/links must match the business.
5. Store `instagram_match_confidence` separately from `instagram_profile_exists`.

False positives are the main danger. Common names like "Caribe", "Luna", "Selina", "Jaguar", "Roots", "Tasty", "Salsa", "Bamboo", "Pura Vida", and "Cocles" can match unrelated accounts. Identity checks matter more than raw hit count.

Open databases of IG handles:

- OSM `contact:instagram` tags are the best legitimate structured source already available.
- Business websites often link official IG.
- Facebook pages often cross-link IG, but scraping/searching Facebook at scale is brittle.
- Local tourism directories may include social URLs.
- There is no generally reliable, legal, open, comprehensive Instagram handle database for cross-reference.

Recommendation: run handle guessing only after mining websites/OSM/PVS/Maps pages, and only for businesses still missing IG. Cap guesses and require identity evidence.

## 4. WhatsApp verification

The plan's "near-zero risk" assessment is too optimistic.

`wa.me` links are intended for user navigation, not bulk account enumeration. Bulk-testing hundreds of phone numbers can look like enumeration, especially if done from the same IP/session with uniform timing. The public behavior of WhatsApp web endpoints also changes, and some checks may require JS, cookies, or app redirects. A page response is not a stable proof that the number is an active WhatsApp Business account.

Practical approach:

- Prefer explicit WhatsApp links found on PVS, websites, OSM tags, Instagram bios, Facebook pages, or Maps website fields.
- For normalized Costa Rica numbers, infer `whatsapp_candidate=true` only when the business publishes the phone as a mobile-style contact or uses "WhatsApp" text.
- If verification is necessary, do a tiny paced batch, e.g. 20-30 numbers/day, randomized delays, no login, no message sending.
- Do not try to automate WhatsApp Web with an account. That introduces account-ban risk.

I would split fields:

- `whatsapp_url_published`: found explicitly in source.
- `whatsapp_candidate_url`: constructed from phone.
- `whatsapp_verified`: only if a robust check confirms it.
- `whatsapp_verification_method`: source, wa.me check, manual, etc.

## 5. Risk assessment

### Lowest risk

- PVS cache mining.
- Existing SQLite/CSV extraction.
- OSM tag extraction from already-downloaded files.
- Parsing existing screenshots/logs.
- Crawling 81 real business websites politely.
- Extracting contact links from already-known business websites.

### Low to medium risk

- Booking.com, TripAdvisor, Expedia, Agoda, Hostelworld lookups at low volume.
- Direct Google Maps CID page loads for known CIDs with conservative pacing.
- Local tourism directory crawling.

These can still burn time through blocks, JS complexity, and data ambiguity, but account/IP risk is manageable if no login is used.

### Medium to high risk

- Google Search for 615 queries.
- Google Maps search result automation.
- Instagram profile probing at scale.
- Facebook search by phone.
- Airbnb scraping.
- TikTok searching/scraping.
- WhatsApp `wa.me` bulk verification.

The risk is not only permanent IP blocks. It includes CAPTCHA walls, stale cookies, browser fingerprint flags, account lockouts if logged in, poisoned results, and silent partial data.

### I would deprioritize/remove

- Twitter/X discovery: low local-business value, high noise.
- TikTok discovery for all 615: high false positive rate; only do known tourism/restaurant brands if needed.
- Facebook search by phone at scale: brittle and likely to require login or trigger abuse detection.
- Couchsurfing: not a business directory.
- Bulk WhatsApp verification: replace with published-link extraction plus candidate marking.
- Airbnb listing extraction for all lodging: high duplicate/host/listing ambiguity. Use only for named villas/cabinas where the business name is distinctive.

## 6. Phase ordering

The proposed Day 1-14 order spends too early on speculative social/platform discovery. I would reorder:

### Day 1: deterministic/local extraction

- PVS cache mine.
- OSM tags extraction.
- Parse existing grid/vision artifacts for any hidden coordinates/CIDs.
- Normalize and deduplicate phones, domains, social URLs.
- Classify websites as real business domains vs OTA/social/affiliate.

### Day 2: business-owned web presence

- Crawl real business websites.
- Extract emails, phones, WhatsApp links, social links, schema.org, OpenGraph metadata.
- Use website links to verify Instagram/Facebook identity.

### Day 3: known Maps assets

- Direct CID page extraction for existing CIDs.
- Do not use Search yet.
- Extract phone, website, hours, status, review count, categories, plus any outbound links available.

### Day 4: targeted platform enrichment

- Booking/Hostelworld/Agoda/Expedia only for hotels, hostels, and named vacation rentals.
- Viator/GetYourGuide/TripAdvisor Experiences only for tour companies.
- Restaurant directories only for restaurants.

### Day 5: cautious social gap-fill

- Instagram guessing for records still missing IG after owned-source extraction.
- Strict candidate caps and identity checks.
- Facebook only from explicit cross-links, not broad phone search.

### Days 6-14: resolve geometry/CID gap

If Google Search risk is acceptable, prioritize:

1. 134 grid names first, because they lack coordinates.
2. 31 OSM additions missing CIDs.
3. 100 PVS missing CIDs.

If Google Search risk is not acceptable, do not spend these days on social extras. Instead, try non-Google geocoding evidence: OSM/Nominatim from existing OSM data, business websites with embedded maps, Booking/TripAdvisor/Hostelworld coordinates, and local directory address pages. Expect lower completeness.

## 7. The Google Search question

There is no guaranteed realistic free way to automate 615 Google searches over 10-20 days without blocks. It may work if done slowly in a real browser with a stable residential IP and human-like behavior, but it is not "safe"; it is "maybe tolerated until it is not."

Permanent blocking is less likely than repeated CAPTCHA, degraded results, temporary IP/session throttling, and browser profile reputation damage. If a Google account is logged in, account risk becomes the main concern. I would not use a valuable personal Google account for this.

For the 134 grid names, accepting no CIDs is a poor outcome because they remain barely usable. But I would not resolve them with 615 broad searches. Use a narrower plan:

- Search only the 134 grid names first.
- Include area context in the query to reduce repeated reformulation.
- Stop once a CID/coordinate is captured.
- Limit to small manual/semi-automated batches.
- Treat it as a separate, explicitly risk-accepted phase.

Alternative methods:

- Re-open the original grid scan artifacts/screenshots and infer approximate coordinates from the grid cell that produced each discovery.
- Use Maps URLs already present in browser history/logs if captured by the scanner.
- Use OSM/Overpass refresh and name matching.
- Use business websites with embedded Google Maps if found through non-Google sources.
- Use OTA/TripAdvisor pages that expose coordinates for lodging and restaurants.
- Use local directories with address/area pages.

Best answer: do not run 615 Google searches. Run deterministic extraction first, then decide whether the remaining 134 justify a carefully paced, risk-accepted Maps/Search recovery pass.

## Revised priority list

1. Mine local PVS SQLite and cached HTML.
2. Fully extract OSM contact/social/email tags.
3. Classify and crawl real business websites.
4. Extract known Google Maps CID pages directly.
5. Use lodging/tour/restaurant-specific platforms only for relevant categories.
6. Resolve the 134 grid names' coordinates/CIDs through the lowest-risk available path.
7. Only then run Instagram guessing with strict identity verification.
8. Avoid broad Twitter/TikTok/Facebook/WhatsApp enumeration unless a later use case specifically needs those fields.

## Final recommendation

Revise the plan around provenance and risk tiers, not around platform enthusiasm. The target should be a defensible directory, not maximum field fill rate. A smaller number of high-confidence URLs and coordinates is more valuable than hundreds of guessed social/platform links with weak identity evidence.

The current strategy can work if narrowed. The main changes I would make are:

- Downgrade WhatsApp bulk verification from "near-zero risk" to "avoid unless tiny/manual."
- Downgrade Instagram guessing from "low risk" to "low request risk, medium false-positive risk."
- Remove broad Twitter/X and TikTok discovery from the core plan.
- Treat visual scraping tools as optional pilots, not operational dependencies.
- Move known-CID Maps extraction earlier.
- Prioritize making the 134 grid records geospatially usable before enriching already-usable records.
