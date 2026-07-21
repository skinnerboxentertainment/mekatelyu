# Change Log

The baseline audit was read-only. Corrective work began only after the user authorized a reduced directory-only launch base. No commit, push, deployment, or canonical business-record edit has been performed.

| Date | Change | Finding / initiative | Files | Verification | Status |
|---|---|---|---|---|---|
| 2026-07-20 | Created launch-readiness audit documentation | Audit control | `audit/launch-readiness/` | File and Git status inspection | Documentation only |
| 2026-07-20 | Moved audit records outside the Pages working tree | PUB-001 / INIT-016 | `audit/launch-readiness/` | Audit record integrity check | Implemented locally |
| 2026-07-20 | Moved map enrichment input out of generated/public output | PUB-001 / INIT-016 | `paradisio_app/data/maps_parsed_v3.json` | Clean generator read | Implemented locally |
| 2026-07-20 | Established dedicated `release/paradisio_app` output and stale-output cleanup | PUB-001 / INIT-016 | `paradisio_app/build.py`, `.gitignore` | Minimal artifact inventory | Implemented locally |
| 2026-07-20 | Removed payment, claims, classifieds, public privileged modes, invoices, analytics, and incomplete language UI from reduced build | PAY-001, PRIV-001/002, FUNC-001, I18N-001, AUTH-001, CLASS-001 | Generator/static output | Forbidden-surface scan | Implemented locally; closure retest pending |
| 2026-07-20 | Restricted WhatsApp to explicit valid destinations and suppressed contact actions for closed businesses | DATA-001/002 | `paradisio_app/build.py` | Generated route/status profile pending | Implemented locally |
| 2026-07-20 | Simplified visitor hierarchy/cards, normalized presentation labels, improved contrast/focus/motion, and added map failure state | MOB-001, A11Y-001, visual critique | Generator and static assets | Browser regression pending | Implemented locally |
| 2026-07-20 | Restored QR as a required directory feature and generated one direct-profile QR per business | User scope clarification | `paradisio_app/build.py`, `requirements.txt` | 771 profiles / 771 QR; zero missing/orphaned | Implemented and mechanically verified |
| 2026-07-20 | Added source-data, release-artifact, QR, URL, metadata, CSP, budget, and vendor-integrity gates | QA-001, DATA-001/002, PUB-001, SEC-001/002 | `scripts/`, `tests/` | 13 unit tests + two verifiers pass | Implemented locally |
| 2026-07-20 | Added CI-only launch workflow that builds and uploads the candidate without deployment | QA-001, OPS-001 | `.github/workflows/launch-readiness.yml` | Local command parity passes; remote run pending | Implemented locally |
| 2026-07-20 | Moved directory payload to an external static asset and prohibited inline scripts | PERF-001, SEC-001 | Generator/release verifier | 5.5 KB HTML shell; CSP browser retest pass | Verified locally |
| 2026-07-20 | Self-hosted pinned Leaflet and MarkerCluster with SHA-256 manifest | SEC-002 | `paradisio_app/static/vendor/` | Vendor hashes + directory/detail map regression pass | Verified locally |
| 2026-07-20 | Added minimal deployment root preserving `/paradisio_app/`, custom 404, robots, sitemap, and `.nojekyll` | PUB-001, SEO-001, OPS-001 | Generator | Deployment-root verifier pass | Implemented locally |
| 2026-07-20 | Added privacy-conscious public correction issue template and links | DATA-003 | `.github/ISSUE_TEMPLATE/`, generator | Link/browser presence check | Implemented locally; owner monitoring pending |
| 2026-07-20 | Added 76 screenshot-verified exact WhatsApp matches to previously empty records | DATA-001/002; WhatsApp reconciliation | `pv_master_unified.csv`, `scripts/integrate_validated_whatsapp.py`, integration manifest | 106→182 explicit routes; exact 76-cell source diff; 30 tests; source/release verifiers | Implemented and verified locally |
| 2026-07-20 | Added versioned semantic taxonomy, evidence packets, visibility matrix, additive groups/tags/attributes, semantic search, and quality filtering | INIT-021 / DATA-003 | `paradisio_app/semantic_taxonomy.py`, semantic index, build/UI, audit artifacts, tests | 771/771 indexed; zero orphans; 23 review-only cases; desktop/mobile browser pass | Implemented and verified locally |
| 2026-07-20 | Resolved all 23 flagged primary-category decisions with an evidence-backed 19-correction/4-retention ledger | INIT-021 / DATA-003 | `pv_master_unified.csv`, `scripts/resolve_taxonomy_decisions.py`, `audit/semantic-taxonomy/resolved-primary-categories.csv` | Exact 19-category-cell diff; unresolved queue zero; 45 tests; browser category/mixed-use pass | Implemented and verified locally |
| 2026-07-20 | Added 55 screenshot-verified, exact, unique, non-colliding Google Maps CIDs and linked their captured text to evidence packets | INIT-021 / DATA-003 | `pv_master_unified.csv`, `scripts/discover_missing_maps_cids.py`, `scripts/reconcile_discovered_maps_cids.py`, `audit/maps-cid-discovery/` | 113/113 captures; 113/113 hashes; 33 collisions and 25 lower-confidence cases quarantined; full regression | Implemented and verified locally |
| 2026-07-20 | Reconciled all 27 CID collision clusters: four ownership transfers, 23 alias/duplicate queues, and two cross-wired website removals | INIT-021 / DATA-003 | `pv_master_unified.csv`, `scripts/reconcile_cid_collisions.py`, `audit/maps-cid-discovery/collision-decisions.csv` | Exact holder/target assertions, screenshot hashes, idempotent dry run, full regression | Implemented and verified locally |
| 2026-07-20 | Consolidated 23 reviewed same-CID alias clusters, preserving all source rows and conflicts in an audit archive | DATA-003 / launch data quality | `pv_master_unified.csv`, `scripts/consolidate_cid_aliases.py`, alias archive/manifest, count gates | 29 aliases archived and removed; 742 canonical rows; unique CIDs; 742 profiles/QR; 48 tests and browser pass | Implemented and verified locally |
| 2026-07-20 | Completed broader multi-signal entity resolution and consolidated four additional deterministic duplicate pairs | DATA-003 / launch data quality | `scripts/audit_entity_resolution.py`, `scripts/resolve_entity_candidates.py`, `audit/entity-resolution/`, master/count gates | 142/142 pairs dispositioned; 4 merges archived; 738 profiles/QR; 713 unique CIDs; 51 tests | Implemented and verified locally |
| 2026-07-20 | Resolved the remaining 25-record Maps/evidence queue and integrated 13 identity-supported unique CIDs | INIT-021 / DATA-003 | `scripts/discover_missing_maps_cids.py`, `scripts/resolve_remaining_maps_evidence.py`, `audit/maps-cid-discovery/current-25/`, decision ledger/report, semantic evidence loader, tests | 25/25 hash-backed captures; 13 accepted and 12 rejected; evidence-poor 25→12; 726 unique CIDs; 54 tests | Implemented and verified locally |
# 2026-07-20 — WhatsApp audit tooling

- Added an offline WhatsApp route audit and machine-readable evidence register.
- Added normalization tests for local numbers, `wa.me`, and `api.whatsapp.com` formats.
- Did not bulk-probe WhatsApp and did not infer WhatsApp capability from ordinary phone fields.
- Added mandatory PNG/JPEG visual evidence validation, SHA-256 hashing, a direct batch recorder,
  and a local visual review index for AutoVisualWhatsAppCheckifier attempts.

# 2026-07-20 — Validated WhatsApp integration

- Added a fail-closed integration utility that accepts only the 76 exact candidate matches,
  requires an empty master target, validates the audited route, and re-hashes its screenshot.
- Wrote `audit/whatsapp-checkifier/integrated-strong-matches.csv` as the exact change manifest.
- Added only those 76 normalized destinations. Ten probable matches were deliberately excluded.
- Rebuilt the directory artifact without changing the business/profile or QR cardinality.
