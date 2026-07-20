# Third-pass evidence — 2026-07-20

Scope: accessibility/responsive source checks, public-artifact boundary, repository hygiene, dependency posture, catalog integrity, classifieds freshness, SEO and payload profiling. Product code and data were not modified.

## Accessibility and responsive checks

- Home exposes one `nav` and one `footer`, but no `main` or `header` landmark. Search, four filters, and the mode selector have no programmatic labels in the inspected accessibility tree.
- No `:focus-visible` or `prefers-reduced-motion` rule was found. Search removes the default outline and supplies only a border-color focus treatment.
- Token contrast: faint text on sand `2.54:1`; coral on white `3.74:1`; muted text on sand `4.45:1`, below WCAG AA `4.5:1` for normal text.
- At 320×568 there was no horizontal overflow. Fixed-control overlap remains separately recorded.
- Automated Tab traversal repeatedly returned to the autofocus search field. Browser automation may be responsible, so this is a manual-test limitation, not a confirmed defect.

## Public deployment boundary

- GitHub Pages publishes all of `master:/docs`.
- `docs/` contains 2,538 files totaling 53.66 MiB; `docs/paradisio_app/` accounts for 2,500 files and 52.20 MiB.
- The public tree includes raw/export datasets, GeoJSON, audit output, enrichment checkpoints, CID samples, internal strategy/build/roadmap/postmortem documents, invoice/admin artifacts, and the application.
- Large published working artifacts include 3.42 MB and 3.35 MB map checkpoint/enrichment JSON files, a 1.75 MB business JSON asset, and several other intermediate files.

## Repository and release hygiene

- 110 commits; 2,940 tracked files totaling about 110.4 MB; Git pack about 91.16 MiB.
- Tracked development artifacts include eight `CODEX_ENDPOINT/sessions` JSON files plus `stealth_session.log` and `stealth_results.jsonl`.
- A limited all-history scan for strong credential prefixes/private-key markers found no confirmed credential. Apparent `sk-` matches were false positives from a `super-sk-playa...` slug. This is not a complete secret audit.
- `requirements.txt` uses bounded version ranges but supplies no lockfile or hashes.
- Leaflet 1.9.4 and MarkerCluster 1.5.3 are version-pinned from `unpkg.com`, but generated tags have no Subresource Integrity hashes.
- GitHub reports `master` is not protected.

## External dependency sample

- Representative Leaflet, MarkerCluster, GoatCounter, and FormSubmit endpoints responded successfully.
- Sampled HTTP business URLs behaved inconsistently: several redirected to HTTPS, two remained HTTP-only, and one affiliate redirect returned `403` to HEAD.
- Code invokes `L.map(...)` without a discovered guard, so loss of the Leaflet CDN can break maps; static list content limits likely impact.

## Catalog integrity profile

- 771 businesses. Duplicate signals: normalized name 4 groups/8 rows; phone 44/99; WhatsApp 44/101; Instagram 6/14; exact coordinates 14/33; duplicate Maps CID 0.
- Malformed email fields: 70, usually `https:address@example.com`; some resemble scraped error-telemetry or asset strings. Malformed website fields: 1.
- Invalid generated Costa Rica WhatsApp routes: 99, confirming `DATA-001`.
- Coordinates present: 631. Relative to `(9.655, -82.753)`, 70 are over 5 km, 10 over 10 km, and the maximum is about 22.88 km. Eight supplied distances differ from recomputation by over 250 m.
- Verification dates present: 640. At launch, 391 will be older than 180 days and 99 older than 365 days; oldest is 2022-05-26.
- Status: 609 active, 130 unknown, 29 needs verification, 3 closed. Category identifiers have inconsistent casing.

## Classifieds profile

- 16 records; all active; none has an expiry field.
- 14 of 16 contain `5555` placeholder phone/WhatsApp numbers.
- Five contain explicit July/August dates; multiple July events/rides will be stale by launch.
- Posted dates span only 2026-07-01 through 2026-07-11, consistent with seed/demo data rather than a live stream.

## SEO and payload profile

- 1,700 HTML files: canonical 750; meta description 924; H1 950; Open Graph 0; Twitter Card 0.
- `index.html`: 1,393,240 bytes raw, 181,810 local gzip-9. Business JSON: 1,754,727 raw, 185,773 local gzip-9. Compression does not eliminate duplicate parse/memory work.
