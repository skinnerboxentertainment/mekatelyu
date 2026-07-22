# Angel Investment Page — Design

## URL

`https://www.whappin.com/invest/`

A single-page static HTML file at `release/invest/index.html`.

## Structure

```
Hero — tagline, one-liner, live app link
  │
Problem — PV has no unified directory
  │
Solution — opt-out directory + QR + WhatsApp routing
  │
Traction — 737 businesses, 726 CIDs, 175 WhatsApp, live site stats
  │
Business Model — 3 tiers (premium, AI add-ons, QR affiliate)
  │
Moat — proprietary dataset, zero API costs, audit trail
  │
Market — CR tourism stats, replicable to 10+ CR towns
  │
Use of Funds — table (affiliate network, WhatsApp concierge, scanner port)
  │
Team — Oscar AF, why this matters
  │
Ask + CTA — mailto / GitHub issue template / Calendly
  │
Footer — links to app, data audit, GitHub
```

## Design tone

Matches the existing Whappin aesthetic (sand, jungle green, coral) but with
a slightly more serious/ambitious feel. Single column, generous whitespace.
No hero image — text-first, Craigslist-honest.

## Key stats to feature

```
737 businesses listed
726 Google Maps CIDs (98%)
175 explicit WhatsApp routes
54 automated tests passing
Zero infrastructure costs
```

## CTA mechanism

A GitHub issue template (`investor-inquiry.md`) that collects:
- Name
- Email
- LinkedIn / AngelList
- Check size range
- Message

Mailto fallback: `oscar@whappin.com` (or whatever the real email is)

## Where it lives

`release/invest/index.html` — built by `build.py`, deployed with the rest of
the site. No separate repo needed. No backend needed.

## Build impact

- Add `invest/` page to `build.py`
- Add `investor-inquiry.md` issue template
- No changes to CSP, no new dependencies, no external scripts
