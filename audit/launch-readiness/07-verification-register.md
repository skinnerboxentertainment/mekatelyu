# Verification Register

This register distinguishes implementation from verified closure. A finding remains open until its acceptance criterion is retested and evidence is recorded.

| Verification ID | Finding | Baseline / retest | Procedure | Result | Evidence | Date |
|---|---|---|---|---|---|---|
| VER-001 | Build baseline | Baseline | Clean isolated generation and artifact comparison | Pass | 2,500 paths; timestamp-only variance | 2026-07-20 |
| VER-002 | Internal links | Baseline | Resolve generated internal references | Pass | 12,326/12,326 resolved | 2026-07-20 |
| VER-003 | Python syntax | Baseline | AST-parse all Python files | Pass | 70/70 | 2026-07-20 |
| VER-004 | Critical browser smoke | Baseline | Home/search/detail/map/claim/premium/admin/dashboard/classifieds | Pass with findings | No sampled app console error; journey findings logged | 2026-07-20 |
| VER-005 | Live provenance | Baseline | Compare Pages configuration and live deployment commit | Pass | Live deployment matches `6f40dd80`; HTTPS enforced | 2026-07-20 |
| VER-006 | Branch protection | Baseline | Query GitHub branch protection | Fail | `master` not protected | 2026-07-20 |
| VER-007 | Data invariants | Baseline | Profile contacts, status, duplicates, distance, freshness | Fail | DATA-001/002/003 | 2026-07-20 |
| VER-008 | Classified lifecycle | Baseline | Profile contact placeholders, status, dates, expiry | Fail | CLASS-001 | 2026-07-20 |
| VER-009 | Accessibility fundamentals | Baseline | DOM/a11y inventory, CSS contrast/focus/motion scan | Fail | A11Y-001; manual keyboard retest remains | 2026-07-20 |
| VER-010 | Public artifact boundary | Baseline | Inventory all Pages-published files | Fail | PUB-001 | 2026-07-20 |
| VER-011 | Reduced artifact scope | Retest | Scan generated release for excluded surfaces/data | Pass locally | 1,548+ minimal app files at initial check; forbidden markers zero | 2026-07-20 |
| VER-012 | QR one-to-one invariant | Retest | Compare profile and 300×300 QR slug sets | Pass locally | 771/771; zero missing/orphaned | 2026-07-20 |
| VER-013 | Contact/status invariants | Retest | Build from canonical CSV; validate explicit WA, normalized calls, closed actions | Pass locally | 106 WA, 626 calls, closed actions zero | 2026-07-20 |
| VER-014 | Launch-rule unit tests | Retest | Python unittest discovery | Pass locally | 13/13 | 2026-07-20 |
| VER-015 | Reduced release verifier | Retest | Boundary, paths, metadata, CSP, QR, URLs, budgets, vendor hashes | Pass locally | `scripts/verify_release.py` | 2026-07-20 |
| VER-016 | Desktop/mobile browser regression | Retest | Search/filter/map/detail/closed/QR at 1440, 390, 320 | Pass locally | Browser interaction + screenshots | 2026-07-20 |
| VER-017 | Dependency self-hosting | Retest | Hash vendor assets; load directory/detail maps under CSP | Pass locally | Leaflet/MarkerCluster manifest + browser | 2026-07-20 |
| VER-018 | CI workflow | Retest | Execute GitHub Actions build and upload | Pending authority | Requires push | — |
| VER-019 | Production release and rollback | Retest | Approved deploy, smoke, rollback rehearsal | Pending authority | Not authorized | — |
| VER-020 | Strong WhatsApp integration | Retest | Guarded evidence-to-master integration and content-level CSV diff | Pass locally | 76/76 additions; only 76 `whatsapp` cells changed; 10 probable matches excluded | 2026-07-20 |
| VER-021 | Post-integration release integrity | Retest | Rebuild, unit suite, source verifier, release verifier, QR/profile counts | Pass locally | 30 tests; 182 explicit WA; 771 profiles; 771 QR | 2026-07-20 |
| VER-022 | Semantic evidence/index integrity | Retest | Join master/CID evidence; validate keys, provenance, primary-category preservation, and group coverage | Pass locally | 771 unique records; zero group orphans; 23 review-only conflicts | 2026-07-20 |
| VER-023 | Semantic discovery behavior | Retest | Desktop/mobile browser test of shortcuts, hostel membership, facet, synonym search, overflow, and enriched profile | Pass locally | Stay 386 after false-positive correction; Hostel 23/23; Café 36; semantic synonym search; 390×844 no overflow | 2026-07-20 |
| VER-024 | Taxonomy decision resolution | Retest | Evidence review, guarded canonical patch, exact source diff, regeneration, regression, and browser category checks | Pass locally | 19 corrections; 4 retentions; 0 unresolved; 45 tests | 2026-07-20 |
# WhatsApp route audit — 2026-07-20

- Command: `.venv\\Scripts\\python.exe scripts\\audit_whatsapp_routes.py`
- Result: PASS — 106 explicit routes normalized, 0 malformed routes, 0 omitted exact-match
  first-party crawl candidates.
- Evidence: `evidence/whatsapp-route-audit.csv` and `evidence/whatsapp-route-audit.md`.
- Safety: no messages sent; no master-data mutation; no bulk account probing.
- Control finding: an existing candidate and impossible `+50600000000` both produced HTTP 200
  generic send pages, so HTTP resolution was rejected as a verification signal.
- Follow-up queue: four numbers are shared across multiple listings. These are retained because
  shared booking/property-management contacts can be legitimate, but ownership should eventually
  be confirmed through the business-correction workflow.

# Regression verification — 2026-07-20

- Command: `.venv\\Scripts\\python.exe -m unittest discover -s tests -v`
- Result: PASS — 17 tests.
- Command: `.venv\\Scripts\\python.exe scripts\\verify_release.py`
- Result: PASS — reduced release verified at `release/paradisio_app`.
- Command: `git diff --check`
- Result: PASS; only existing line-ending conversion warnings were emitted.

# AutoVisualWhatsAppCheckifier pilot — 2026-07-20

- Queue preparation: PASS — 106 preservation, 523 candidate, and 6 pilot records.
- Visible target matches: 2.
- Number-only/inconclusive established targets: 3.
- Negative control: correctly rejected as confirmation evidence.
- Messages sent: 0.
- Dataset mutations: 0.
- Ledger: local `audit/whatsapp-checkifier/ledger.jsonl` (intentionally gitignored).
- Evidence follow-up: PASS — all six pilot attempts were rerun with persistent JPEG captures.
- Integrity: each image-backed ledger entry records the relative path, byte length, and SHA-256 hash.
- Human review index: local `audit/whatsapp-checkifier/REVIEW.md` renders every image with its
  classification and evidence summary.

# Full WhatsApp evidence verification — 2026-07-20

- Coverage: PASS — 106/106 established, 523/523 candidates, and 1/1 control.
- Screenshot integrity: PASS — 630/630 latest-record screenshots match their stored SHA-256.
- Capture errors: 0 unresolved.
- Messages/calls/logins: 0.
- Regression suite: PASS — 28 tests.
- Reduced release verifier: PASS.
- Results: `audit/whatsapp-checkifier/FULL-AUDIT-REPORT.md`.
- Reconciliation data: `audit/whatsapp-checkifier/reconciliation.csv`.
- Visual review: `audit/whatsapp-checkifier/REVIEW.md` and gitignored `screenshots/`.

# Validated WhatsApp integration verification — 2026-07-20

- Guarded dry run: PASS — 76 unique exact-match record IDs with hash-valid screenshots.
- Source diff: PASS — 771 rows unchanged in count; exactly 76 changed cells, all in `whatsapp`.
- Exclusion check: PASS — 0/10 probable-match candidates populated.
- Build: PASS — 182 explicit WhatsApp routes and 626 valid call routes.
- QR/profile invariant: PASS — 771 business pages and 771 direct-profile QR images.
- Regression suite: PASS — 30 tests.
- Source-data verifier: PASS.
- Reduced-release verifier: PASS.
- `git diff --check`: PASS (informational Windows line-ending warnings only).
- Messages, calls, pushes, and deployments: 0.

# Semantic re-enrichment verification — 2026-07-20

- Evidence coverage: 771 master descriptions; 658 linked full CID texts; 511 parsed subcategories;
  198 websites; 113 records queued as evidence-poor.
- Artifact integrity: PASS — 771 unique semantic keys exactly match the 771 master records.
- Canonical preservation: PASS — zero primary-category rewrites, removals, merges, or exclusions.
- Discovery coverage: PASS — every record has at least one broad group; all canonical lodging maps
  to Stay.
- Review controls: PASS — 23 cross-category identities are explicit review records.
- Browser: PASS — shortcut counts, type/quality facet, search synonyms, and mobile layout operate in
  the rebuilt local release.
- Upgrade behavior: PASS after correction — versioned app/data/style asset URLs prevent stale cached
  filtering logic after taxonomy releases.
- Semantic-pass regression at that stage: PASS — 43 tests, source-data verifier, reduced-release verifier, and
  `git diff --check` all pass. The release contains 771 profiles, 771 QR codes, and 182 explicit
  WhatsApp routes.

# Taxonomy decision-resolution verification — 2026-07-20

- Decision completeness: PASS — all 23 flagged records have a recorded disposition and rationale.
- Canonical corrections: PASS — 19 category changes: 7 vacation rentals, 5 wellness, 4 hotels,
  and 3 transport businesses.
- Reviewed retentions: PASS — 3 legitimate mixed-use records and 1 false-positive name inference.
- Unresolved semantic review queue: 0.
- Master diff scope: PASS — 19 `category` cells and the earlier 76 `whatsapp` cells; no other cells.
- Browser: PASS — Wellness 5/5, Transport 3/3, and Selvin's retains Restaurant while remaining
  discoverable under Stay. Browser console warnings/errors: 0.
- Final regression: PASS — 45 tests, source-data verifier, reduced-release verifier, QR/profile
  cardinality, and `git diff --check`.

# Missing-CID discovery and integration verification — 2026-07-20

- Search coverage: PASS — 113/113 evidence-poor records processed.
- Capture stability: PASS — zero errors, challenge pages, or no-result states.
- Evidence integrity: PASS — 113/113 screenshots present and matching their recorded SHA-256.
- Raw results: 88 exact, 15 probable, 10 ambiguous.
- Guarded reconciliation: PASS — 55 exact, unique, non-colliding CIDs applied; 33 CID-collision
  records and 25 probable/ambiguous records held without mutation.
- Master coverage after integration: 713/771 records have a CID.
- Semantic evidence: the 55 accepted visible-text captures are linked into evidence packets; raw
  navigation text remains ineligible for automatic tag inference.
- Release invariants: PASS — 771 profiles, 771 per-establishment QR codes, 182 explicit WhatsApp
  routes, 45 tests, source-data verifier, reduced-release verifier, and `git diff --check`.
- Browser regression: PASS — a newly enabled profile (`Taller Gabriel`) exposes the expected CID
  Maps URL and QR image; desktop and 390×844 mobile views have no horizontal overflow; search and
  all five filters remain available; browser console warnings/errors: 0.
- External effects: zero messages, calls, paid API requests, pushes, or deployments.

# CID collision reconciliation verification — 2026-07-20

- Scope: PASS — 27/27 distinct collision CIDs have a recorded disposition.
- Ownership: PASS — four exact-match CIDs transferred from mismatched legacy holders to their
  screenshot-verified target; each CID remains present exactly once in the master.
- Alias safety: PASS — 23 alias/duplicate clusters received no additional CID and no record deletion.
- Contact cleanup: PASS — only the two demonstrably cross-wired former-holder website fields were cleared.
- Repeatability: PASS — rerunning the reconciliation dry run recognizes the post-transfer state and
  proposes no additional mutation.

# Field-preserving alias consolidation verification — 2026-07-20

- Scope: 23/23 reviewed alias clusters; 29/29 redundant alias rows.
- Preservation: every removed row and every canonical before/after state is stored verbatim in the
  private JSONL archive; conflicts are summarized in the CSV manifest.
- Canonical cardinality: 742 unique establishments after consolidation.
- CID invariant: every populated Google Maps CID occurs exactly once.
- Public-contact safety: personal/PR contacts and a hotel-level review URL identified during the dry
  run were retained only in the archive, not promoted to canonical public fields.
- QR contract: one regenerated establishment-specific QR per canonical profile.
- Final regression: PASS — 48 tests, source-data verifier, reduced-release verifier, and
  `git diff --check`; 742 profiles and 742 QR images.
- Browser: PASS — home reports `50 of 742 results`; removed `Cabinas KiMiMi` alias is absent;
  canonical Geckoes Lodge retains its CID Maps action, QR, and absorbed validated WhatsApp route;
  horizontal overflow and console warnings/errors: 0.

# Broader entity-resolution verification — 2026-07-20

- Pair coverage: 142/142 candidate pairs have explicit decisions and rationales.
- Dispositions: 4 deterministic merges; 121 distinct-CID relationships; 8 related/shared-contact
  relationships; 9 rejected single-signal duplicate hypotheses.
- Preservation: four removed rows plus canonical before/after states archived verbatim.
- Canonical cardinality: 738 records; every populated CID remains unique.
- Merge examples: Jaguar's official site and contact fields retained; Douglasville inherits its
  captured CID; Chile Rojo inherits the alias Instagram identity.
- Evidence-poor canonical records after all consolidation: 25.
- Release invariants: PASS — 738 profiles, 738 establishment-specific QR images, 713 unique CIDs,
  175 explicit WhatsApp routes, 51 tests, source-data verifier, release verifier, and `git diff --check`.

# Remaining Maps/evidence queue verification — 2026-07-20

- Capture coverage: PASS — 25/25 current evidence-poor records received fresh Google Maps captures;
  zero runner errors.
- Evidence integrity: PASS — each decision is tied to its capture and SHA-256-backed screenshot.
- Raw classifications: 3 exact, 12 probable, and 10 ambiguous; these were treated as review aids,
  not automatic authorization to mutate canonical data.
- Final dispositions: 13 accepted identity-supported matches and 12 rejected wrong-target or
  insufficient results. Every queued record has one explicit disposition and rationale.
- CID safety: PASS — the 13 accepted CIDs are present, rejected candidates were not injected, and
  every populated canonical CID remains unique.
- Semantic linkage: PASS — only accepted current-run capture text is eligible as a provenance-bearing
  evidence source; screenshot/result mismatch or hash failure stops the build.
- Final coverage: 726/738 canonical records have CIDs; 12 remain evidence-poor without speculative
  enrichment.
- Release invariants: PASS — 738 profiles, 738 establishment-specific QR images, 175 explicit
  WhatsApp routes, 54 tests, source-data verifier, reduced-release verifier, and `git diff --check`.
- External effects: zero messages, calls, paid API requests, commits, pushes, or deployments.
