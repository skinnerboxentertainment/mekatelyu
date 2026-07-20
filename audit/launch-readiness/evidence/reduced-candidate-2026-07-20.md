# Reduced release-candidate evidence — 2026-07-20

Branch: `launch/aug1-directory-base`
State: local and uncommitted; not pushed or deployed
Target artifact: `release/`

## Scope encoded in the build

Included: directory home, search/filter/sort, list/map views, 771 business profiles, contact links that pass launch rules, 771 direct-profile QR codes, sitemap, robots, root redirect, and custom 404.

Excluded from the generated artifact: payment/premium, claims/forms, classifieds/posting, invoices/admin, owner modes, analytics, internal scores, incomplete localization controls, raw datasets, enrichment checkpoints, and audit/research documents.

## Mechanical verification

- Release verifier: PASS.
- Source-data invariant verifier: PASS.
- Unit tests: 13/13 PASS.
- Business profiles: 771.
- QR PNGs: 771 at 300×300; zero missing and zero orphaned.
- Internal references: zero broken.
- Forbidden launch markers: zero.
- HTTP references: zero.
- Canonical/Open Graph/CSP coverage: every directory/profile HTML page.
- Inline scripts: zero.
- Homepage shell: 5,543 bytes.
- Public directory data asset: 508,076 bytes.
- Repeated fixed-date final builds produced identical deployment-tree SHA-256 `74e86e3a90f54301505b8516c5a88e9a7376ce0f90c9440060141b2c50c4daff`.
- Vendored Leaflet 1.9.4 and MarkerCluster 1.5.3 assets match the committed SHA-256 manifest.

## Contact and status rules

- WhatsApp is emitted only from an explicit source WhatsApp field: 106 routes.
- Valid normalized call routes: 626.
- Primary actions: 520 Call, 106 WhatsApp, 70 Instagram, 59 Map, 11 Website, 5 None.
- All three closed records have no primary or secondary contact action.
- Invalid external URLs and nine invalid Instagram handles are omitted rather than guessed.
- HTTP-only business destinations are omitted rather than rewritten to unverified HTTPS endpoints.

## Browser regression

- Desktop home at 1440×1000: two-column result composition, search-first hierarchy, no prototype controls.
- Mobile home at 320×568 and 390×844: search and primary controls appear in the first viewport; no horizontal overflow observed.
- Search `cacao`: 7/7 results.
- Clear all: clears search and filters, restoring 50/771 initial results.
- Services shortcut: 32/32 results, including real-estate grouping; raw identifiers are not presented.
- Directory map: 631/771 geocoded records.
- Representative profile: local map, QR block, secondary actions, and mobile sticky CTA render.
- Closed profile: closed state and QR render; no WhatsApp/Call/Instagram contact action.
- Self-hosted Leaflet/MarkerCluster retest: directory and detail maps pass under CSP.
- Final artifact: 1,563 files / 5.93 MiB, including 771 profiles and 771 QR PNGs.

## Controls still pending

- Remote CI execution and artifact review require a push.
- Branch protection, Pages source migration, deployment approval, production smoke test, and rollback drill require repository/deployment authority.
- Legacy `docs/` and tracked session/log artifacts remain in the repository pending an approved cleanup/history decision.
- Catalog deduplication, stale/unknown-record disposition, and real-world sampling remain content-governance work; ambiguous records were not changed autonomously.
- Manual screen-reader/physical-device testing and legal/privacy ownership decisions remain.
