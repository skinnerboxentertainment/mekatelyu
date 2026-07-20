# Audit Log

All times use America/Costa_Rica unless otherwise noted.

| Date | Activity | Result / evidence |
|---|---|---|
| 2026-07-20 | Cloned `skinnerboxentertainment/mekatelyu` | Clean `master` at `6f40dd80`, tracking `origin/master` |
| 2026-07-20 | Established audit controls | Read-only baseline agreed; documentation-only writes authorized |
| 2026-07-20 | Read repository operating instructions | `AGENTS.md` reviewed; canonical data/generator and safety constraints recorded |
| 2026-07-20 | Initial repository inventory | Static GitHub Pages product; canonical CSV, Python generator, generated `docs/`, historical QA artifacts identified |
| 2026-07-20 | Created controlled audit record | `docs/launch-readiness/` initialized; application and production data unchanged |
| 2026-07-20 | Isolated clean build from Git archive | Pass: generator completed at baseline commit and produced 771 businesses, 16 classifieds, and 2,500 files |
| 2026-07-20 | Compared clean rebuild with committed generated app | Pass with expected variance: same 2,500 paths; only `index.html` and `data/metrics.json` changed, both solely due to generated timestamp |
| 2026-07-20 | Test discovery | Finding: `pytest` is declared but unavailable in both host runtimes; no conventionally named test suite or CI workflow exists |
| 2026-07-20 | Python syntax baseline | Pass: all 70 Python files parsed successfully with Python 3.13 AST parser |
| 2026-07-20 | Internal generated-link scan | Pass: 12,326 local `href`/`src` references across 1,700 HTML files resolved to existing files |
| 2026-07-20 | Dataset structure/profile | 771 rows, 34 columns; no blank names, invalid coordinate pairs, malformed explicit emails, or future verification dates detected by baseline rules |
| 2026-07-20 | Generated contact-route profile | Finding: 629 generated WhatsApp routes, of which 99 are not valid `506` + 8-digit Costa Rica routes; source CSV has only 106 explicit WhatsApp values |
| 2026-07-20 | Closed-business behavior check | Finding: all 3 `closed` records still generate WhatsApp as the primary action |
| 2026-07-20 | Desktop browser: home/search/detail | Search for `cacao` returned 7 results; detail page, map, and internal navigation rendered; no application console error observed |
| 2026-07-20 | Owner/payment/admin/classified browser review | Findings: placeholder posting email, placeholder SINPE number, public invoice/admin data, and unauthenticated privileged-mode links confirmed |
| 2026-07-20 | Mobile browser at 390×844 | No horizontal overflow; finding confirmed where fixed mode selector overlaps fixed primary WhatsApp bar |
| 2026-07-20 | Language-control interaction | Finding: selecting Español changes `<html lang>` to `es` but visible navigation, tagline, and search placeholder remain English |
| 2026-07-20 | Metadata/security-header source scan | No CSP or referrer policy in generated HTML; primary business pages lack canonical and social-card metadata; further hosting-header assessment pending |
| 2026-07-20 | Accessibility control inventory | Finding expanded: home page has no `main`/`header`; search, four filters, and mode selector lack programmatic labels; language state is not exposed |
| 2026-07-20 | External-reference inventory | 11,045 external references, 3,392 unique URLs; 109 HTTP references representing 95 unique insecure URLs require normalization/validation |
| 2026-07-20 | Live GitHub Pages verification | Production URL loaded successfully at commit `6f40dd80`; live page confirms placeholder Post address and public Admin mode |
| 2026-07-20 | GitHub Pages configuration | Legacy Pages build from `master:/docs`, public, HTTPS enforced, no CNAME, no custom 404; latest build succeeded in 24.05 s |
| 2026-07-20 | Analytics/privacy inventory | GoatCounter included on 1,692 pages; claim form sends name/email/phone and listing changes to FormSubmit; no privacy/legal artifact or form disclosure found |
| 2026-07-20 | Local payload timing sanity check | Uncompressed localhost: index 1,393,240 bytes / 260 ms; JSON 1,754,727 bytes / 38 ms. This is not a constrained-network performance score |
| 2026-07-20 | Accessibility/CSS deep pass | Missing control names/landmarks, no focus-visible/reduced-motion rule, and failing sample contrast ratios recorded; automated Tab traversal marked inconclusive |
| 2026-07-20 | Pages publication-boundary inventory | Finding: 2,538 files/53.66 MiB publicly mix product, datasets, checkpoints, audits, internal documents, and privileged artifacts |
| 2026-07-20 | Dependency and external endpoint sample | CDN endpoints responded; no SRI or browser fallback; sampled HTTP links include redirects, HTTP-only targets, and an affiliate HEAD 403 |
| 2026-07-20 | Repository/history hygiene | Tracked sessions/logs/checkpoints found; limited strong-token/private-key history scan found no confirmed credential |
| 2026-07-20 | GitHub branch-control check | Finding: `master` is not protected |
| 2026-07-20 | Deep catalog integrity profile | Findings: 70 malformed emails, duplicate signals, 70 records beyond 5 km, 99 records over one year stale at launch, 8 distance discrepancies, 130 unknown statuses |
| 2026-07-20 | Classifieds lifecycle profile | Finding: all 16 active/no expiry; 14 placeholder `5555` contacts; date-specific July content remains active |
| 2026-07-20 | Generated SEO/payload census | 1,700 HTML: canonical 750, description 924, H1 950, social metadata 0; gzip estimates documented |
| 2026-07-20 | Consolidated decision and Aug 1 critical path | Assessment complete; current no-go; reduced directory-only scope recommended for the target window |
| 2026-07-20 | Dedicated visual/product critique | Live desktop/mobile hierarchy, design tokens, cards, details, controls, and sense of place assessed; separate critique and reduced-release composition documented |

## Residual verification and decision work

- Manual keyboard/screen-reader and representative physical-device testing.
- Field or throttled performance measurement against an agreed budget.
- Exhaustive external-link testing under a rate-limited release check.
- Rollback execution, which would mutate deployment/repository state and was outside read-only authorization.
- Owner/legal decisions for payment, privacy, analytics, provenance, moderation, retention, and terms.
- All remediation implementation and independent closure retests.
# 2026-07-20 — WhatsApp route preservation and validation

- Preserved the reduced release rule that exposes WhatsApp only from an explicit source value.
- Reconciled all 771 launch records against 191 results from the prior website crawl.
- Found 17 crawled WhatsApp links, all already represented in the 106 explicit master routes;
  therefore no inferred phone routes were added and no established routes were removed.
- Tested one existing candidate and the impossible control `+50600000000` through `wa.me`.
  Both returned HTTP 200 and the same generic WhatsApp send-page redirect, proving that this
  passive probe is not a reliable account-existence check. No message was sent.
- Added `scripts/audit_whatsapp_routes.py`, an offline evidence report that never contacts a
  business or changes the master dataset.

# 2026-07-20 — AutoVisualWhatsAppCheckifier pilot

- Implemented the local queue generator, append-only ledger API, resume dashboard, negative
  control guard, and separation between 106 established routes and 523 phone candidates.
- Ran a six-route visible-browser pilot at single-route concurrency with no message text.
- Two routes exposed matching named profiles: Cabinas Guarana → `Hotel Guarana`, and the
  shared Cariblue route → `Cariblue Beach and Jungle Resort`.
- Three established routes exposed only a formatted phone number and were logged `unclear`.
- The impossible `+50600000000` control also exposed a number-only generic send page. This
  confirms that a number-only page cannot establish account availability or ownership.
- Zero messages, calls, form submissions, master-data changes, or release-data changes occurred.

# 2026-07-20 — Full WhatsApp visual audit

- Completed visible-browser inspection of all 106 established WhatsApp routes, all 523 separate
  normalized-phone candidates, and one negative control.
- Captured and SHA-256 verified 630/630 local screenshots with zero unresolved capture errors.
- Established results: 30 name matches, 7 probable aliases, 63 different visible names, and
  6 number-only/inconclusive pages. Existing explicit routes were preserved pending review.
- Candidate results: 76 strong name matches, 10 probable name matches, and 437 different visible
  identities. No candidate was added to the directory.
- Created an authority-tail queue of 162 decisions: 76 established-route exceptions and 86
  proposed candidate additions.
- Zero messages, calls, WhatsApp Web logins, source-data edits, or release-data edits occurred.
- The built-in browser completed the pilot but its screenshot channel became unreliable during
  scale-up. The run switched to dedicated local Playwright/Chromium after a tested three-route
  smoke pass; the same navigation-only safety boundary was retained.

# 2026-07-20 — Strong WhatsApp match integration

- Integrated the 76 `phone_candidate` records classified as exact visual `match` into the local
  canonical dataset after validating record identity, empty targets, candidate routes, and each
  screenshot's SHA-256 hash.
- Explicit WhatsApp coverage increased from 106 to 182 of 771 businesses. The 10
  `probable_match` candidates and all 437 mismatches remained untouched.
- Rebuilt the reduced directory release. All 771 business profiles and all 771 per-profile QR
  codes remain present.
- This was a local-only change: no commit, push, deployment, message, or call was performed.

# 2026-07-20 — Semantic re-enrichment and discovery pass

- Joined all 771 master records to existing local descriptions, parsed CID evidence, and full CID
  capture text. Linked full-text CID evidence exists for 658 records; 113 evidence-poor records were
  separated for a future targeted sweep.
- Built a versioned multi-label taxonomy separating primary category, broad discovery groups,
  specific establishment types, and evidence-backed attributes.
- Corrected an early model that allowed amenities such as a hotel gym to redefine establishment
  identity; identity and attribute assertions now have separate promotion rules.
- Added provenance and confidence to every accepted inferred assertion. No canonical category,
  business name, listing status, merge, deletion, or exclusion was applied.
- Indexed 771/771 establishments, with zero discovery orphans. Twenty-three cross-category identities
  are retained in a review queue rather than receiving automatic primary-category rewrites.
- Rewired the local release to search tags/attributes/synonyms, added a type-or-quality filter, and
  made visitor shortcut groups count actual multi-label membership.
- Browser verification confirmed 23/23 canonical hostels under Stay and 36 Café facet results.
  After the focused lodging-identity expansion, Stay initially contained 387 establishments; final
  decision review removed one false-positive `Casita` inference, producing the verified count of 386.
  Mobile at 390×844 had no
  horizontal overflow and retained all semantic controls.
- Browser testing detected stale cached application logic after a rebuild; versioned asset URLs were
  added so the new taxonomy controls activate for returning visitors.

# 2026-07-20 — Resolution of 23 taxonomy decisions

- Reviewed all 23 cross-category records against canonical descriptions, parsed CID fields, focused
  full-text CID evidence, and establishment identity.
- Applied 19 canonical primary-category corrections: 7 to `vacation_rental`, 5 to `wellness`,
  4 to `hotel`, and 3 to `transport`.
- Retained four existing primaries after review: Arrecife and Selvin's remain restaurants with Stay
  as a secondary group; Le Caméléon remains a hotel with Eat/Nightlife secondary visibility; La
  Casita de Monli remains a restaurant after correcting a false lodging inference from its name.
- Regenerated all semantic artifacts. The unresolved taxonomy review queue is now zero.
- Content-level master comparison confirms exactly 19 category cells plus the previously approved
  76 WhatsApp cells differ from the repository baseline; no other master field changed.
- Browser verification confirmed 5/5 corrected Wellness listings, 3/3 Transport listings, and
  retained mixed-use visibility for Selvin's under both Restaurant identity and Stay discovery.

# 2026-07-20 — Targeted 113-record Google Maps CID discovery

- Searched all 113 evidence-poor directory records directly in Google Maps using business name,
  area, Limón, and Costa Rica. The resumable run completed without a CAPTCHA, wall, or capture error.
- Preserved 113 screenshots, resolved URLs, visible text captures, observed Maps names, match scores,
  extracted CIDs, and SHA-256 evidence hashes.
- Raw classification produced 88 exact, 15 probable, and 10 ambiguous results.
- Reconciliation identified 33 exact results whose CID was already assigned elsewhere in the master
  dataset. These were quarantined because they include both legitimate aliases and apparent legacy
  CID misassignments; neither class is safe for blind bulk mutation.
- Applied 55 exact, unique, non-colliding CIDs to records whose master CID was still empty. Held all
  25 probable/ambiguous records and all 33 collision records for review.
- Linked captured full text for the 55 accepted discoveries into semantic evidence packets, while
  retaining the existing prohibition on using noisy raw Maps navigation text for automatic tags.
- This was local-only: no commit, push, deployment, paid API, message, call, or business contact.

# 2026-07-20 — Reconciliation of 27 CID collision clusters

- Reviewed every discovered record and existing master holder across 27 distinct shared CIDs using
  captured Maps identity plus local names, areas, phones, websites, descriptions, and alternate-name evidence.
- Classified 23 clusters as duplicate/alias candidates. The CID remains only on the established
  canonical holder; no alias received a duplicate CID and no record was merged or deleted.
- Corrected four legacy CID ownership errors: El Sol del Caribe from Flor del Caribe; Casitas Mar y
  Luz from Hidden Jungle Beach House; Las Casitas de Playa Negra from Douglasville Guesthouse; and
  Uva Blue Jungle Villas from Villa Laurel.
- Cleared two cross-wired websites from former holders: `casitasmaryluz.com` from Hidden Jungle and
  `uvabluevillas.com` from Villa Laurel. Other independent holder contact data was preserved.
- Added a hash-gated, idempotent reconciliation utility and a permanent 27-cluster decision ledger.

# 2026-07-20 — Field-preserving consolidation of 23 alias clusters

- Consolidated 23 reviewed same-CID clusters into their existing canonical CID-bearing records and
  removed 29 redundant alias rows, reducing the canonical launch directory from 771 to 742 establishments.
- Archived every removed row verbatim together with each canonical row's before/after state. Conflicting
  phone, area, category, social, and URL values remain retrievable in the private audit archive.
- Filled useful missing canonical fields, including two validated WhatsApp routes, two Instagram handles,
  official sites for ATEC, Le Caméléon, Café Rico, and Azul/Repazul, and selected business contact fields.
- Did not promote a personal Casa Palliata booking email, a Da Lime PR email, or the hotel-level Aguas
  Claras TripAdvisor record into public canonical fields; those values remain in the verbatim archive.
- Rebased profile, QR, semantic, source, and release invariants to the reviewed 742-record canonical set.

# 2026-07-20 — Broader multi-signal entity resolution

- Compared all 742 consolidated records across normalized/fuzzy names, phone, WhatsApp, Instagram,
  website host, exact/near coordinates, and Google Maps CID identity.
- Resolved all 142 candidate pairs: 4 deterministic duplicates, 121 pairs retained because separate
  CIDs establish distinct Maps identities, 8 related/shared-contact pairs retained, and 9 weak
  single-signal pairs rejected as duplicates.
- Consolidated Hotel Cariblue into Cariblue Beach and Jungle Resort; Refugio de animales Jaguar into
  Jaguar Rescue Center; Douglas Ville guest house into Douglasville Guesthouse; and Chili Rojo into
  Chile Rojo. All four removed rows and canonical before/after states are archived verbatim.
- Preserved legitimate co-located or related operations such as Namu/Ka Namu, Río Negro/Rio Home,
  hotel restaurants, property-management portfolios, and separate police locations.
- Canonical directory after the broader sweep: 738 establishments.

# 2026-07-20 — Remaining Maps/evidence queue resolution

- Re-ran all 25 remaining evidence-poor canonical records through a fresh, navigation-only Google
  Maps capture. The run completed 25/25 without capture errors and preserved a screenshot, resolved
  URL, visible text, extracted identity, and SHA-256 evidence hash for every attempt.
- The raw automated pass classified 3 results as exact, 12 as probable, and 10 as ambiguous. No
  probable or ambiguous result was accepted solely from its machine label.
- Accepted 13 identity-supported Maps results after comparing captured identity with canonical name,
  area, description, contacts, translations, and documented former names. Added those 13 unique CIDs.
- Rejected 12 wrong-target or insufficient results, including room-level listings, host properties,
  similarly named businesses, and generic place searches. Those records remain unmodified and
  explicitly documented instead of receiving speculative CIDs.
- Evidence-poor canonical records fell from 25 to 12; unique CID coverage rose from 713 to 726 of
  738 establishments. The release remains at 738 profiles, 738 establishment-specific QR codes, and
  175 explicit WhatsApp routes.
