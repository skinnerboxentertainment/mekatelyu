# Sponsorship System — Design Document

## Overview

A lightweight, self-serve sponsorship system for Whappin Puerto Viejo.
Direct-sold ad slots powered by a JSON file — no backend, no external scripts,
no tracking. Fully static-site compatible.

---

## Constraints

| Constraint | Implication |
|---|---|
| GitHub Pages (static only) | No server-side ad rotation, no database, no PHP |
| CSP `script-src 'self'` | No external ad network JS allowed |
| Zero budget | No paid services, no ad network fees |
| Local relevance | Ads must be Puerto Viejo businesses, not global |
| Privacy-first | No cookies, no tracking pixels, no analytics |
| Mobile-first | Ads must work on small viewports |
| QR codes & offline | Sponsors can also get QR-linked ad placements |

---

## Data Model

A single JSON file at `paradisio_app/data/sponsors.json`:

```json
[
  {
    "id": "selvins-2026-08",
    "name": "Selvin's Restaurant & Cabinas",
    "tagline": "Caribbean cuisine on Punta Uva beach",
    "url": "https://www.whappin.com/businesses/selvin-s-restaurant-and-cabinas-playa-punta-uva-puerto-viejo-lim-n-costa-rica-pu.html",
    "image": "sponsors/selvins.webp",
    "placement": "sidebar",
    "starts": "2026-08-01",
    "ends": "2026-09-01",
    "type": "sponsor"
  },
  {
    "id": "featured-caribe-horse",
    "name": "Caribe Horse Riding Club",
    "tagline": "Guided beach rides — all levels welcome",
    "url": "https://www.whappin.com/businesses/caribe-horse-riding-club-playa-negra-puerto-viejo-lim-n-costa-rica-playa-negra.html",
    "image": null,
    "placement": "featured",
    "starts": "2026-08-01",
    "ends": "2026-10-01",
    "type": "sponsor"
  }
]
```

### Fields

| Field | Required | Description |
|---|---|---|
| `id` | yes | Unique slug for the sponsorship |
| `name` | yes | Business name (displayed) |
| `tagline` | no | Short line (displayed below name) |
| `url` | yes | Target link (business page or external) |
| `image` | no | Path to sponsor image (optional) |
| `placement` | yes | `"sidebar"`, `"featured"`, or `"footer"` |
| `starts` | yes | First day of campaign (ISO date) |
| `ends` | yes | Last day of campaign (ISO date) |
| `type` | yes | `"sponsor"` or `"featured"` |

---

## Placement Slots

### 1. Sidebar card (desktop only)
- Shows on business detail pages, right column on desktop
- One card: sponsor logo + name + tagline + link
- Rotates randomly among active `"sidebar"` sponsors on each page load
- Hidden on mobile (sidebar collapses)

**Mock:**
```
┌─────────────────────┐
│  [logo]             │
│                     │
│  Sponsored by       │
│  Selvin's Restaurant │
│  Caribbean cuisine  │
│  on Punta Uva beach │
│                     │
│  [Visit →]          │
└─────────────────────┘
```

### 2. Featured listing (inline, mobile-friendly)
- `"featured"` sponsors get a subtle badge in search results
- `"⭐ Sponsored"` tag on the result card
- Also boosts the business to the top of its category results

### 3. Footer bar (compact, all pages)
- One line: `"Sponsored by Selvin's Restaurant · [Learn more]"`
- Rotates on page load
- Minimal visual weight

---

## Implementation

### Files to add

| File | Purpose |
|---|---|
| `paradisio_app/data/sponsors.json` | Sponsor data (git-tracked) |
| `paradisio_app/static/sponsors.css` | Sponsor card styles |
| `paradisio_app/static/sponsors.js` | Client-side rotation logic |

### Files to modify

| File | Change |
|---|---|
| `paradisio_app/build.py` | Add sponsor section to business page template (sidebar) |
| `paradisio_app/static/styles.css` | Import sponsor styles |
| `paradisio_app/static/app.js` | Add featured badge rendering to search results |

### Build pipeline

```
sponsors.json ──► build.py reads and embeds sponsor data into:
                   ├── businesses/{slug}.html (sidebar slot)
                   └── static/directory-data.js (featured flags for search)
                   sponsors.js reads from embedded data at runtime
```

No separate build step. Sponsors are rebuilt on every `python build.py` run.

---

## Sponsor Image Handling

Images are stored at `release/sponsors/` and tracked in git.

- Accepted formats: WebP (preferred), PNG fallback
- Max dimensions: 300×200 px for sidebar, 60×60 for featured
- Optimized manually before committing (or via a script)
- A missing image shows a text-only card (still functional)

---

## How Selling Works (Operational)

1. You agree on price/terms with a local business
2. You add their entry to `sponsors.json` with dates
3. Optionally add their logo image to `paradisio_app/data/sponsors/`
4. Commit, push → CI rebuilds and deploys
5. Their sponsorship goes live within 2 minutes
6. Ads auto-expire based on `ends` date (JS checks and hides expired)

No third party, no platform fees, no minimums. You own the inventory.

---

## CSP Impact

Sponsors are served from `'self'` — no CSP changes needed.

If a sponsor links externally (e.g., their own website), that link opens via
`target="_blank" rel="noopener"` — already compliant.

If a sponsor wants to serve their own image from their own server, we'd need
to add `img-src` to CSP. Default approach: self-host all sponsor images.

---

## Timeline Estimate

| Task | Time |
|---|---|
| Create `sponsors.json` + validation | 20 min |
| Add sidebar card to business page template | 30 min |
| Add footer bar to all pages | 15 min |
| Write `sponsors.js` rotation logic | 30 min |
| Write `sponsors.css` styles | 20 min |
| Add featured badge to search results | 20 min |
| Test with sample sponsors | 20 min |
| **Total** | **~2.5 hours** |

---

## Viability Assessment

| Criterion | Verdict |
|---|---|
| Works with GitHub Pages | ✅ |
| Compatible with CSP | ✅ |
| No external dependencies | ✅ |
| No budget required | ✅ |
| Mobile-friendly | ✅ |
| Easy to sell/update | ✅ (edit JSON, commit, push) |
| Auto-expiry | ✅ |
| Trackable? | No — no click tracking. Honest link clicks only. |
| Scalable? | Yes — JSON can hold hundreds of sponsors |
| Competes with our listings? | No — sponsors are clearly marked as paid |

## Click Tracking

Three options, from simplest to most capable:

### Option 1: UTM param (zero infrastructure)

Sponsor links include `?ref=whappin` in the URL. The sponsor sees the
traffic source in their own analytics (Google Analytics, Instagram Insights,
etc.). We don't need to count anything.

**Free. Private. Works immediately. No CSP changes.**
**Downside:** we never see the counts — sponsor has to tell us.

### Option 2: Client-side count with localStorage

When a user clicks a sponsor link, the JS:
1. Increments a counter in localStorage for that sponsor
2. Shows an admin-only summary when a secret query param is present
   (`?stats=1` on the home page)

**Free. Privacy-safe (no data leaves the browser).**
**Downside:** counts are per-device, not global. Only useful for
approximate trends. Resets if user clears browser data.

### Option 3: GoatCounter event tracking (recommended for real reporting)

We already excluded GoatCounter from the reduced release artifact, but we
could add it back **exclusively for sponsor clicks** — no pageviews, no
session tracking, just click events.

A lightweight beacon fires when a sponsor link is clicked:
```javascript
fetch("https://gc.whappin.com/count", {
  method: "POST",
  body: JSON.stringify({
    event: "sponsor-click",
    sponsor: sponsorId
  })
})
```

This requires:
- Adding `connect-src https://gc.whappin.com` to CSP
- Signing up for a free GoatCounter account (already done — we had it before)
- The reduced release would no longer be "analytics-free" but sponsor clicks
  are low-volume and privacy-light (no personal data, no cookies)

**Free. Global counts. Report-ready for sponsors.**
**Downside:** minimal CSP change, one external request per click.

### Recommendation: Option 1 (UTM) for launch, Option 3 (GoatCounter events) when you sell your first slot and need to report numbers.

---

## Recommendation

**Viable for launch.** The system is simple, cheap, and fully under your
control. It doesn't compromise the site's privacy, performance, or
appearance. Build it in 2.5 hours, sell the first slot in 30 minutes.

Start with UTM params (zero work). Add GoatCounter event tracking when a
sponsor asks "how many clicks did I get?" — that's a 15-minute addition.
