# Paradisio — Executive QA Summary & Action Plan

> **Source:** Combined findings from `audit_entries.py` (rules-based) + `codex_audit_review.json` (adversarial AI review)  
> **Date:** 2026-07-11  
> **Dataset:** 772 businesses across master CSV → build → app

---

## Overall Health

| Metric | Value | Interpretation |
|--------|:-----:|---------------|
| Total entries | 772 | Stable |
| With issues (any) | 626 | 81% need at least one fix |
| Critical issues | ~45 CID reuse groups | **Blocking data integrity** |
| High issues | ~50 | Routing-breaking, needs attention |
| Medium issues | ~393 | Quality polish, high ROI |
| Avg score (my audit) | 87.2% | Overstated — missing CID reuse check |

---

## Priority 1 — Blockers (fix now, unblocks everything downstream)

### 1.1 Shared CID ownership (🔴 45 groups)

**Problem:** 45 Google Maps CIDs are shared by multiple unrelated businesses. This means:
- Maps links point to the wrong business
- Ratings/addresses/hours shown are for the wrong entity
- Enrichment data is cross-contaminated  
- **CID-keyed features are unreliable until fixed**

**Notable examples:**

| CID | Shared by | Issue |
|:---:|-----------|-------|
| 4837747133838124638 | Blue Dreams Hotel, Le Cameleon Boutique Hotel, Le Caméléon, Vista Verde | 4 different businesses, same CID |
| 9838950680602433731 | Hotel Punta Cocles, Playa Chiquita Paradise, Villa del Mar, Villa Laurel, Uva Blue Jungle Villas | 5 records, likely unrelated |
| 8515965990195848246 | Casitas Mar y Luz, Estrellas Cabinas, Hidden Jungle Beach House, Hotel Posada Nena | 4 lodging records |
| 13864196564288057579 | Clínica San Gabriel (medical) + Taller Gabriel (workshop) | Completely unrelated businesses |

**Fix:** Group all 45 → select canonical entity per CID → remove or correct contaminated CIDs → re-run enrichment.  

**ROI:** Unblocks every CID-dependent feature (ratings, addresses, maps links).

### 1.2 Closed businesses still live (🔴 3 entries)

**Problem:** Permanently closed businesses are discoverable and scorable.

| Business | Status |
|----------|--------|
| Lapalapa Beach Front Hotel | permanently_closed |
| Totem Hotel Resort & Restaurant | permanently_closed |
| Samurai Fusion | closed |

**Fix:** Flag closed records. Either remove from directory or show prominent "Closed" badge.

**ROI:** Trust. A tourist showing up at a closed business will not come back.

### 1.3 Duplicate entity records (🔴 ~10 pairs)

**Problem:** Same business appears twice with different IDs/slugs. This fragments search, splits reviews, and confuses users.

| Group | Detail |
|-------|--------|
| Geckoes Lodge | Two records, same name + CID, different categories/areas/coords |
| The Amazing Treehouse & Nature | Two records, shared name + description |
| Cafe Rico / Café Rico | Unicode normalization collision |
| Chile Rojo / Chili Rojo | Spelling variant |
| Hotel Rustika Lodge / Rustika Lodge | Partial/abbreviated name |
| KiMiMi / KiaMiMi / KlaMiMi | Multiple spelling variants |
| Cabinas Talamanca + Hotel Creek | Duplicate-likely pairs |

**Fix:** Deduplicate by CID, normalized name, coordinates, phone, and website. Merge records.

**ROI:** Eliminates duplicate effort across all future work.

---

## Priority 2 — High ROI / Quick Wins

### 2.1 Concatenated WhatsApp numbers (🟡 2 entries)

**Problem:** Two businesses have two phone numbers concatenated into one WhatsApp field.

| Business | Value |
|----------|-------|
| Centro Médico Aruma | `+50686555082+50684480274` |
| Dragonfly Beach Retreat | `+50661287817+16479208454` |

**Fix:** Split into separate WhatsApp numbers or pick the primary.

**ROI:** 5-minute fix, unblocks WhatsApp routing for these businesses.

### 2.2 Email in website field (🟡 1 entry)

**Problem:** `alain01barisy@gmail.com` stored in website column for Panadería Francés.

**Fix:** Move to email field.

**ROI:** 2-minute fix.

### 2.3 Website without scheme (🟡 1 entry)

**Problem:** `www.hotellossuenos.com` — link tag will be invalid without `https://`.

**Fix:** Prepend `https://` in build.py or the CSV.

**ROI:** 2-minute fix.

### 2.4 Placeholder descriptions (🟡 31 entries)

**Problem:** 31 businesses have descriptions like "Discovered via ..." — raw provenance text that leaked into the public description field.

**Fix:** These came from the original PV Satellite import. Replace with template-generated descriptions (we already have the `generate_descriptions.py` pipeline for this).

**ROI:** 30-minute fix, immediately improves 31 business pages.

---

## Priority 3 — Systematic Quality

### 3.1 Missing normalized phone (⚪ 218 entries)

**Problem:** 218 businesses have a phone number but no `normalized_phone`. This affects WhatsApp routing and tel: link generation.

**Fix:** Add a build-time normalization step that strips non-digit characters from phone and writes to `normalized_phone`.

**ROI:** Medium effort (add to build.py), unifies contact routing for 28% of listings.

### 3.2 Missing coordinates (⚪ 144 entries)

**Problem:** 144 businesses have no lat/lng — no map pin, no distance sorting, no geofilter.

**Fix:** Run through the geofilter/coordinate pipeline (many have CIDs but no extracted coords).

**ROI:** High visibility impact — map is a primary navigation feature.

### 3.3 Missing area (⚪ 153 CSV rows)

**Problem:** 153 master CSV rows have no area set. Shows as "Unknown" in the app.

**Fix:** Infer from coordinates, name keywords, or OSM tags.

**ROI:** Quick win, improves filter and browse experience.

---

## Priority 4 — Enrichment & Parsing

### 4.1 Capture links/images/JSON-LD (P1)

**Problem:** The v2 enrichment captures full text but not links, images, or structured data. This means menus, booking URLs, reservation links, and photo URLs are lost.

**ROI:** Unlocks routing data that Maps provides but we discard.

### 4.2 Address parser (23% coverage)

**Problem:** Only 176/772 businesses have a captured address. The regex confuses Plus Codes with street addresses.

**ROI:** Address is the #1 missing field users expect on a directory page.

### 4.3 Hours parser (8% coverage)

**Problem:** Only 58 entries have operating hours. The "Open now" filter can't work without normalized hours.

**ROI:** Open-now filter is the top requested tourist feature.

---

## Priority 5 — Platform & Monetization

### 5.1 Multi-language AI audit

Generate FR, PT locale files via Codex. Audit existing EN/ES/DE for quality.

### 5.2 Claim/correction form

Already built (`claim.html`) — needs the `CLAIM_EMAIL` configured. One config change, rebuild, push.

### 5.3 Classifieds posting flow

Web3Forms submission form for community-classifieds. Enables community engagement.

---

## 30/60/90 Day Roadmap

| Time | Focus | Key deliverables |
|:----:|-------|-----------------|
| **Now** | 🔴 Data integrity | Fix 45 shared CIDs, remove 3 closed businesses, deduplicate 10+ pairs |
| **Week 1** | 🟡 Quick wins | Fix WhatsApp, email, website issues. Replace 31 placeholder descriptions. Configure claim email. |
| **Week 2** | ⚪ Systematic quality | Normalize 218 phone numbers. Backfill 144 missing coordinates. Assign 153 missing areas. |
| **Week 3** | 🟢 Enrichment | Fix address parser. Improve hours extraction. Add link/image capture. |
| **Month 2** | 🌐 Platform depth | Multi-language locale expansion. Classifieds posting flow. Open-now filter. |
| **Month 3** | 💰 Monetization | Premium listing tiers. Instagram event detection. WhatsApp concierge pilot. |

---

## Raw findings files

| File | Source | Content |
|------|--------|---------|
| `docs/paradisio_app/data/audit_report.json` | `audit_entries.py` | 772 entries scored, issues flagged, fixes suggested |
| `docs/paradisio_app/data/codex_audit_review.json` | Codex adversarial review | 11 gaps found, 14 additional issues, methodology evaluation |

---

*Generated 2026-07-11. Both audits are read-only — no data was modified.*
