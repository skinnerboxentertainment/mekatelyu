# Whappin Puerto Viejo — State of the Project

Date: 2026-07-22
Target launch: August 1, 2026
Lead: Oscar AF

---

## 1. What It Is

Whappin Puerto Viejo is a mobile-first community business directory for Puerto Viejo
de Talamanca, Costa Rica. Every business in town is listed by default (opt-out model).
The site is live at **https://www.whappin.com/**.

It replaces the old Paradisio branding. "Powered by Paradisio" remains in the tagline.

---

## 2. Current Metrics

| Metric | Value |
|--------|-------|
| Total businesses | 737 |
| Google Maps CIDs | 726 (98%) |
| WhatsApp routes | 175 (validated, explicit) |
| Phone numbers | 599 |
| Instagram handles | 444 |
| Active status | 711 |
| Needs verification | 23 |
| Closed | 3 |
| Automated tests | 54 passing |
| Deployment | GitHub Actions — auto-deploys on merge to master |

### Categories

Hotel 198 · Restaurant 191 · Vacation Rental 150 · Services 81 · Shopping 54 ·
Tour Company 27 · Hostel 23 · Real Estate 5 · Wellness 5 · Transport 3

### Areas Covered

Puerto Viejo · Cocles · Cahuita · Playa Negra · Playa Chiquita · Punta Uva ·
Manzanillo · Hone Creek · Bribri · Sixaola · Gandoca

---

## 3. What Exists

### Site Features (shipped)

- **Home page** — search, category filters, area filters, contact-channel filters,
  paginated results, category shortcut tiles, list/map toggle, Leaflet cluster map
- **Business pages** — 737 detail pages with contact routing (WhatsApp, phone,
  Instagram, website, Google Maps), star ratings from Google Maps, semantic tags,
  amenity labels, QR code per business, map with custom branded pin, sticky
  bottom action bar ([Directions] [Call] [Share])
- **Share sheet** — Copy link, WhatsApp, Show QR code, Download QR
- **Sticky nav** — follows you on long business pages
- **404 page** — custom, styled
- **Sitemap + robots.txt** — SEO ready
- **CSP** — strict content security policy, self-hosted Leaflet maps
- **Branch protection** — PRs required, CI checks required, linear history
- **HTTPS enforcement** — enabled
- **Custom domain** — www.whappin.com
- **Angel investment page** — /invest/ with $5K ask, use of funds table, email CTA
- **QA feedback template** — "Report a problem" link on every page → GitHub issue
- **Investor inquiry template** — GitHub issue form for inbound interest

### Data Quality (shipped)

- All 737 records categorized and area-assigned (0 uncategorized, 0 unknown area)
- Amenity normalization: Spanish→English (Wi-Fi gratis → Free Wi-Fi, etc.)
- Lodging amenity inference: Hotels/Hostels/Vacation Rentals without real amenity
  data get statistically-driven defaults. Coverage: 38% → 68%.
- Auto-generated descriptions replaced for 85 records with structured text
- Rating source shown: "from Google Maps"

### Backend / Ops

- GitHub Actions CI/CD — builds, tests, verifies, and deploys on every merge
- 54-unit test suite covering entity resolution, launch rules, WhatsApp audit,
  semantic taxonomy, alias consolidation, remaining evidence
- Release artifact verification — ensures no forbidden surfaces leak into
  production
- Rollback: re-run any prior green CI workflow to restore a previous deploy
- Branch protection: PR review + CI checks + linear history required on master

---

## 4. What Was Removed (Reduced Release Scope)

The audited baseline (`6f40dd80`) was found unsafe for launch. The following
were intentionally removed from the reduced release candidate:

- Payment / premium listing pages
- Claims / business owner verification
- Classifieds posting
- Admin dashboard / privileged modes
- Analytics (GoatCounter)
- Invoice / admin records
- SINPE payment placeholders
- Inferred WhatsApp routes (all WhatsApp now requires explicit validated source)

These can be reintroduced post-launch with proper authorization boundaries.

---

## 5. What's Pending

### Auto-resolving (no action needed)

| Item | Status |
|------|--------|
| `whappin.com` apex SSL cert | DNS needs CNAME update; forwarding removed. Cert auto-provisions up to 24h |
| Enforce HTTPS | Enabled. Done. |

### Should do before Aug 1 (30 min total)

| Item | Effort |
|------|--------|
| Pixel 7a device test | 15 min manual |
| Partner QA session | Walk through, file issues, triage |

### Deferred (not blocking launch)

| Item | Why deferred |
|------|-------------|
| 239 businesses without amenities (restaurants, services, shopping) | No reliable signal to infer. Flagged for future enrichment pass. |
| Screen-reader / keyboard audit | Manual, can do post-launch |
| Full taxonomy revamp | Bigger conversation for post-launch |
| Sponsorship/ad system | Design doc exists, not built |
| Premium listing infrastructure | September target (post-launch) |

---

## 6. Roadmap

### August (Launch + Stabilize)

- **Aug 1:** Launch at www.whappin.com
- Monitor issues via QA feedback template
- Partner QA triage and fixes
- Gather initial user feedback

### September — Commerce Phase

- **Take App evaluation in progress.** Recommended path:
  1. Sign up for Take App free tier
  2. Test SINPE Móvil payment flow end-to-end
  3. Onboard 3-5 local restaurants as pilots
  4. If validated: build premium listing upsell with Take App integration
- Premium listing tier: $15-20/mo per business
- Featured placement upsell
- QR affiliate network development

### Q4 2026 — Growth Phase

- Commerce abstraction layer (support Take App + manual SINPE)
- Scanner port to second Costa Rica town (Tamarindo or Santa Teresa)
- WhatsApp concierge MVP
- $5,000 angel raise (sponsorship/revenue-share)
- Data enrichment pass for remaining 239 thin records

### 2027 — Scale Phase

- Multi-town presence (3-5 CR tourism towns)
- Premium listing network effects
- Community content layer (photos, reviews, tips)
- Revenue sustainability

---

## 7. Key Documents for New Cohort Members

Read in this order:

1. `audit/launch-readiness/13-aug1-release-candidate-handover.md` — authoritative project handover
2. `audit/launch-readiness/11-authority-tail-handoff.md` — owner decisions (all resolved)
3. `audit/launch-readiness/14-launch-record.md` — what shipped
4. `AGENTS.md` — operational protocols
5. `HANDOVER.md` — entry point
6. `docs/paradisio_direction_unified.md` — design direction
7. `docs/take-app-evaluation-complete.md` — commerce strategy research
8. `docs/doc-inventory.md` — full doc audit (Active vs Historical vs Archive)

### Do NOT treat these as current (will poison context):

- `README.md` — stale counts, references old docs/ deployment
- `TURNOVER.md` / `turnover_unified.md` / `turnoverCodex.md` — pre-reduced-release
- `docs/paradisio_status_and_ideas.md` — lists removed features as "built"
- Any `audit/` doc before `13-aug1-release-candidate-handover.md` — baseline evidence,
  not current state

---

## 8. Quick Reference

```
Site:          https://www.whappin.com/
Invest page:   https://www.whappin.com/invest/
GitHub:        https://github.com/skinnerboxentertainment/mekatelyu
Repo branch:   master (protected)
CI/CD:         GitHub Actions — Launch readiness workflow
Domain:        www.whappin.com (CNAME → skinnerboxentertainment.github.io)
Master data:   pv_master_unified.csv (737 rows)
Generator:     paradisio_app/build.py
Contact:       ideaguyinteractive@gmail.com
Investor inqs: GitHub issue → template: investor-inquiry.md
QA feedback:   "Report a problem" link in site footer
```
