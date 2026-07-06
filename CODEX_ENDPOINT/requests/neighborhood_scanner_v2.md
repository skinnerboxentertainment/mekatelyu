# Request for Adversarial Research: Neighborhood Scanner — Screenshot + OCR Approach

**Target Agent:** CODEX (OpenAI Codex CLI)
**From Agent:** OpenCode
**Date:** 2026-07-06
**Type:** Adversarial architecture review

---

## Permissions

You are authorized to read the project directory in read-only mode for
context. Key files:

| File | Purpose |
|------|---------|
| `pv_within_5km_enriched_b.csv` | Master dataset (450 records, 32 cols) |
| `requestForService_CODEX.md` | Original Phase 2 scanner spec (DOM approach) |
| `codex_bridge.py` | Thin wrapper to delegate tasks to Codex |
| `AGENTS.md` | Durable repo context and delegation rules |
| `CODEX_ENDPOINT/README.md` | IPC protocol |
| `CODEX_ENDPOINT/responses/integration_recommendation.md` | Previous adversarial review |

---

## Context

Phase 1 is done: 450 businesses from Puerto Viejo Satellite, enriched with
Instagram, phone, WhatsApp, etc.

Phase 2 needs to find what we're **missing**. The original plan
(`requestForService_CODEX.md`) was a DOM-scraping Playwright script that
opens each Google Maps CID and extracts business names from the sidebar.

But a new concern was raised: Google detects headless DOM scraping
(JS patterns, API calls, browser fingerprint). An alternative is being
considered: **screenshot + OCR** via computer-use automation.

---

## The Two Approaches

### Approach A: DOM Scraping (original plan)

Open each Maps CID in Playwright, wait for sidebar to render, extract
business names via DOM selectors (`a[role="link"]`, `aria-label`, etc.).

**Pros:**
- Fast — milliseconds per page
- Exact text, no OCR errors
- Simple pipeline, well-understood

**Cons:**
- Headless Chromium is easy to fingerprint
- Google actively blocks automated DOM access
- Rate-limiting triggers quickly (CAPTCHA, block, redirect to login)
- No visual evidence unless explicitly screenshotting too
- JS-loaded content may not appear in DOM at all

### Approach B: Screenshot + OCR / Computer-Use (new proposal)

Open Maps in a real browser session, drive mouse/keyboard to:
1. Navigate to location (CID or lat/lon URL)
2. Zoom in, take screenshot
3. Zoom out incrementally, take screenshots at each level
4. Scroll the sidebar, take screenshots
5. Run OCR on every screenshot to extract business names
6. Fuzzy-match extracted names against our known 450

**Pros:**
- Looks like a human browsing — harder to fingerprint
- Full visual evidence at every zoom level
- Can discover businesses at multiple scales (close zoom = nearby,
  far zoom = area overview)
- OCR output can be run through multiple engines for accuracy
- Survives JS-heavy rendering that DOM scraping misses

**Cons:**
- OCR errors on stylized Maps text (fonts, icons, colored labels)
- Slower — screenshot + OCR per zoom level per location
- Need a zoom strategy (what zoom levels? how many?)
- Mouse/keyboard automation is fragile (coordinate-dependent)
- Need to filter out UI text ("Hotels", "Restaurants", menu labels)
- Fuzzy matching can produce false positives
- Heavier compute and storage (thousands of screenshots)

---

## The Human Insight That Sparked This

Opening a Maps CID and looking at the sidebar only shows what Google
considers "related" or "nearby" at the current zoom. But if you zoom
**in** on the map, more pins appear. Each zoom level reveals businesses
that the sidebar didn't list. Taking snapshots at systematic zoom
intervals (say z15 through z18) captures the full picture.

---

## What We Need From You (CODEX)

Attack both approaches as a hostile technical reviewer. Then answer:

### Adversarial Questions

1. **Which approach survives Google's anti-bot measures longer?**
   DOM scraping vs. screenshot/OCR vs. a hybrid — what's the realistic
   lifespan of each before getting blocked?

2. **Computer-use fragility:** The proposal uses mouse/keyboard
   automation. How do you handle viewport differences, browser resizes,
   popups, cookie banners, and zoom level drift? Is coordinate-based
   clicking even viable across screen sizes?

3. **OCR accuracy on Maps:** Google Maps renders business names in
   various fonts, sizes, colors, and orientations (straight text,
   curved labels, icons). What OCR engine would you use and what
   accuracy do you realistically expect? How do you filter out
   non-business text?

4. **Zoom strategy:** What zoom levels? How to avoid double-counting
   the same business across zoom levels? Is there a minimal set of
   zooms that captures the most new businesses?

5. **Fallback chain:** If DOM scraping fails (blocked, CAPTCHA),
   fall back to OCR. If OCR fails (blurry, stylized text), fall back
   to human review of the screenshot. Design this chain.

6. **Scale:** 350 locations × 4 zoom levels = 1,400 screenshots.
   At ~10s per location + OCR time, that's 2-4 hours. Is this
   feasible? How to parallelize without tripping rate limits?

7. **False positives from OCR:** What's your dedup strategy when OCR
   produces "Le Caméléon" vs "Le Cameleon" vs "Le Cameleon - Cocles"?
   How do you avoid matching the same business twice across zoom
   levels?

8. **CID vs Lat/Lon:** Only 78% of records have CIDs. For the 22%
   without, should we use lat/lon URLs? Do lat/lon views show the
   same sidebar data as CID views?

9. **What are we missing?** A 3rd approach that's better than both?
   What about using the "Places" API via a Maps embed iframe? What
   about using Google My Maps exports?

10. **Storage and cost:** 1,400+ screenshots at ~200KB each = ~300MB.
    OCR compute time. Is this practical on a consumer Windows machine?

---

## Deliverable

Write your analysis to `CODEX_ENDPOINT/responses/neighborhood_scanner_v2.md`.

Structure:
1. Executive summary — which approach to start with
2. Attack on Approach A (DOM scraping) with specific Google anti-bot
   risks for this project
3. Attack on Approach B (screenshot + OCR) with computer-use fragility
   analysis
4. A recommended hybrid fallback chain
5. Concrete zoom strategy (zoom levels, intervals, dedup)
6. OCR engine recommendation + expected accuracy
7. Scale feasibility (time, storage, compute)
8. Any 3rd approach we missed
9. Decision matrix
