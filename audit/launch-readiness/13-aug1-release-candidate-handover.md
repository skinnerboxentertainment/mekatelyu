# August 1 Reduced Release Candidate — Full Handover

Status date: 2026-07-20, America/Costa_Rica
Target launch: 2026-08-01
Product: Paradisio / `skinnerboxentertainment/mekatelyu`
Working branch: `launch/aug1-directory-base`
Baseline commit: `6f40dd803c55d8d99f548aa496018934cef5ebfe`
Remote: `https://github.com/skinnerboxentertainment/mekatelyu.git`
State: local, materially modified, uncommitted, unpushed, undeployed

## 1. Executive handover

This workspace contains a mechanically verified **reduced directory-only August 1 release
candidate**. It is not the currently published GitHub Pages build. The public baseline was audited
and found unsafe for launch because it mixed product and internal artifacts and exposed unfinished
payment, claims, classifieds, invoice/admin, analytics, and pseudo-privileged modes. The local
candidate removes those surfaces and retains the useful directory product.

The release candidate currently provides:

- 738 entity-resolved establishment profiles;
- one direct-profile QR code for every establishment;
- search across names, descriptions, semantic tags, attributes, and synonyms;
- broad visitor groups, including complete lodging discovery under Places to Stay;
- type/quality, area, contact-channel, and text filtering;
- list and clustered-map views using locally vendored Leaflet assets;
- validated call, explicit WhatsApp, Maps, website, and social actions;
- closed-business contact suppression;
- canonical/Open Graph metadata, sitemap, robots, CSP, referrer controls, and a custom 404;
- a privacy-conscious GitHub business-correction route.

The candidate passes all local automated gates. It is **not launch-authorized** until another agent
or reviewer inspects the diff, remote CI passes, the exact artifact is approved, GitHub Pages is
migrated from the legacy `master:/docs` publication source, production smoke tests pass, and an owner
accepts rollback responsibility.

## 2. Source-of-truth hierarchy

Use these in this order:

1. `pv_master_unified.csv` — canonical establishment dataset, 738 rows and 34 columns.
2. `paradisio_app/semantic_taxonomy.py` — versioned deterministic taxonomy rules.
3. `paradisio_app/data/semantic_taxonomy.json` — generated semantic index consumed by the build.
4. `paradisio_app/build.py` and `paradisio_app/static/` — release generator and client assets.
5. `release/` — ignored, reproducible output; never treat it as source.
6. `audit/` — private working evidence, decisions, archives, and verification history.

The historical `docs/` tree is the legacy Pages payload, **not** the new candidate. Do not copy new
output back into `docs/` as an informal deployment shortcut. The intended deployment unit is the
allowlisted `release/` artifact produced by the build.

Earlier audit reports preserve what was true at the original baseline. In particular,
`09-final-readiness-report.md` and old counts in baseline evidence are historical. This document,
the latest audit/change/verification log entries, and live verifier output describe current state.

## 3. Exact current metrics

| Measure | Current value |
|---|---:|
| Canonical establishments | 738 |
| Canonical columns | 34 |
| Unique populated Google Maps CIDs | 726 |
| CID coverage | 98.4% |
| Explicit validated WhatsApp routes | 175 |
| Valid normalized call routes | 599 |
| Coordinates | 598 |
| Instagram handles | 444 |
| Facebook URLs | 355 |
| Websites | 182 |
| Booking URLs | 170 |
| Email addresses | 72 |
| TripAdvisor URLs | 64 |
| Active records | 607 |
| Unknown/blank status | 106 |
| Needs verification | 22 |
| Closed | 3 |
| Generated profiles | 738 |
| Generated QR images | 738, each 300×300 PNG |
| Generated release files | 1,497 |
| Generated release size | 6,290,920 bytes |
| Automated tests | 54 passing |
| Unresolved semantic taxonomy decisions | 0 |
| Remaining evidence-poor records | 12 |

Current category counts: hotel 198, restaurant 192, vacation rental 150, services 81, shopping 54,
tour company 27, hostel 23, real estate 5, wellness 5, and transport 3.

Snapshot hashes after the final local rebuild:

- `pv_master_unified.csv`: `F6E4CA2EE6FD24380928A672056C5D3AB441B19CF95FE3EDF1CD2AA826C4571C`
- `paradisio_app/data/semantic_taxonomy.json`: `860B3ADD5BCF1CCF40BFCECE29C337B96A0E5A89DC371C4D45E84D1A84497B85`

Hashes will legitimately change if reviewed data or taxonomy changes. Record replacements in the
verification register.

## 4. What changed from the audited baseline

### Product and release hardening

- Created a dedicated, stale-output-cleaned `release/` deployment root.
- Removed payment/premium, claims/forms, classifieds/posting, public invoice/admin/dashboard,
  pseudo-owner modes, analytics, incomplete language controls, and internal scoring from the reduced
  artifact.
- Moved enrichment input out of the public generated tree.
- Externalized the directory payload instead of embedding the full catalog in the HTML shell.
- Added explicit cache-versioning for application, data, and style assets.
- Self-hosted pinned Leaflet and MarkerCluster files with SHA-256 manifest verification.
- Added CSP, referrer policy, canonical/OG metadata, sitemap, robots, `.nojekyll`, root redirect, and
  custom 404 behavior.
- Added accessible labels, focus treatment, motion handling, contrast/layout improvements, and map
  failure behavior.
- Added a business-correction GitHub issue template.
- Added a CI workflow that builds, verifies, and uploads the candidate but intentionally does not
  deploy.

### Contact safety and WhatsApp

- WhatsApp is generated only from an explicit validated source value. Ordinary phone numbers are
  never silently promoted to WhatsApp.
- International and Costa Rica local-number normalization is tested; invalid targets fail closed.
- Closed establishments expose no primary or secondary contact action.
- Built AutoVisualWhatsAppCheckifier: resumable queues, route capture, screenshots, SHA-256 evidence,
  visual identity decisions, and append-only audit records.
- Integrated 76 screenshot-verified exact WhatsApp matches into previously empty canonical fields.
- Later entity consolidation removed aliases, leaving 175 explicit routes in the current 738-record
  canonical set.
- QR was explicitly retained as a core requirement: every establishment has its own profile QR.

### Semantic taxonomy and discoverability

- Added versioned semantic evidence packets, broad groups, specific tags, attributes, synonyms, and
  provenance for every assertion.
- Search and filters use these additive semantics without silently overwriting primary categories.
- Ensured all hotels, hostels, and vacation rentals surface under Places to Stay.
- Resolved all 23 originally flagged taxonomy decisions: 19 primary-category corrections and four
  reviewed retentions.
- Current semantic review queue is zero.

### Maps/CID enrichment and entity resolution

- Captured and hash-backed the initial 113-record evidence-poor Maps queue.
- Integrated 55 exact, unique, non-colliding CIDs.
- Reconciled 27 CID collision clusters: four ownership transfers, 23 alias/duplicate clusters, and
  two cross-wired website removals.
- Consolidated 23 reviewed same-CID alias clusters, removing 29 redundant rows while archiving every
  removed row and canonical before/after state.
- Ran a broader multi-signal 142-pair entity-resolution sweep and consolidated four further
  deterministic duplicates.
- Freshly captured all 25 remaining Maps/evidence candidates, accepted 13 identity-supported CIDs,
  and rejected 12 wrong-target or insufficient results.
- Canonical count moved from 771 before consolidation to 738; CID coverage is now 726/738 with no
  duplicate populated CIDs.

## 5. Preservation and audit controls

Data consolidation was field-preserving. Removed alias/duplicate rows and canonical before/after
states are archived in private JSONL evidence. Conflicting or personal-looking values were not
blindly promoted into public canonical fields.

Key records:

- `audit/maps-cid-discovery/ALIAS-CONSOLIDATION.md`
- `audit/maps-cid-discovery/alias-consolidation.csv`
- `audit/maps-cid-discovery/alias-row-archive.jsonl`
- `audit/entity-resolution/ENTITY-RESOLUTION-RESULT.md`
- `audit/entity-resolution/pair-decisions.csv`
- `audit/entity-resolution/merged-row-archive.jsonl`
- `audit/maps-cid-discovery/REMAINING-EVIDENCE-RESOLUTION.md`
- `audit/maps-cid-discovery/remaining-evidence-decisions.csv`
- `audit/semantic-taxonomy/resolved-primary-categories.csv`
- `audit/whatsapp-checkifier/integrated-strong-matches.csv`

The signed-in Maps browser profile under `audit/maps-cid-discovery/chrome-profile/` contains local
browser state and is ignored. **Never stage, publish, archive into the repository, or share it.**
Likewise, WhatsApp screenshots and ledgers are ignored because they may display profile information.

## 6. Clean setup and deterministic verification

From repository root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-launch.txt
.venv\Scripts\python.exe scripts\build_semantic_taxonomy.py
.venv\Scripts\python.exe paradisio_app\build.py
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.venv\Scripts\python.exe scripts\verify_source_data.py
.venv\Scripts\python.exe scripts\verify_release.py
git diff --check
```

Expected terminal facts:

- taxonomy: `indexed 738 records; 0 require review`;
- build: `738 businesses`, `738 profile QR codes`, `738 pages`;
- tests: `Ran 54 tests` and `OK`;
- source verifier: 738 businesses, 175 explicit WhatsApps, semantic review queue 0, PASS;
- release verifier: PASS;
- `git diff --check`: no errors; Windows LF→CRLF notices are informational.

CI uses Python 3.13, installs only `requirements-launch.txt`, fixes
`PARADISIO_BUILD_DATE=2026-08-01`, runs the same gates, and uploads `release/` for review.
`requirements-audit.txt` contains optional Playwright tooling and is not a production dependency.

## 7. How to inspect the candidate locally

After building, serve the deployment root—not the source directory or legacy `docs/` tree:

```powershell
.venv\Scripts\python.exe -m http.server 8000 --directory release
```

Open `http://127.0.0.1:8000/`. The root redirects to `/paradisio_app/`.

Minimum browser regression:

1. Confirm home reports 738 total establishments.
2. Search by name and semantic quality; test Stay and Hostel discovery.
3. Exercise group, type/quality, area, and contact filters individually and in combination.
4. Toggle list/map and inspect clustering plus the failure state.
5. Open an active profile and test its available Call, WhatsApp, Maps, website/social links.
6. Confirm its QR displays and points to that exact profile URL.
7. Open a closed profile and confirm no contact actions appear.
8. Test desktop plus 390×844 and 320×568 mobile sizes for overflow/overlap.
9. Check console and failed network requests.
10. Test root redirect, direct profile refresh, sitemap, robots, and 404.

Do not send a WhatsApp message, place a call, submit a form, or contact a business during QA.

## 8. Remaining known gaps and residual risk

### Data/evidence backlog

Twelve canonical records remain evidence-poor because Google Maps returned another business, a
room/host listing, or generic results: Estrellas Cabinas; Ceibo Adventure; Talamanca Chocolate;
Hotel Posada Nena; Paula's and Daniel's Homestay; Panadería Francés; Casa Alegre; Casa Miluca; Boca
Chica; TKD Caribe; Kinawe Cabinas; and Puerto Viejo de Talamanca. Their candidate CIDs were rejected
and not injected. Better independent evidence is required; do not loosen matching thresholds.

The catalog still contains 106 unknown/blank operating statuses and 22 `needs_verification` records.
This is the largest remaining content-governance risk. It is not a mechanical build failure. The
owner must accept this residual risk, authorize a deterministic exclusion policy, or commission
manual review.

### Manual QA backlog

- Real iOS and Android device checks have not been completed.
- A full manual keyboard and screen-reader pass remains outstanding.
- Exhaustive live health checking of every third-party link has not been run.
- Remote GitHub Actions has not run because the candidate is unpushed.

### Repository and operational backlog

- The branch is based on the old commit and all candidate work is still uncommitted.
- The legacy `docs/` publication tree and historical working artifacts require an explicit cleanup
  decision. Do not rewrite Git history without separate authorization.
- `master` branch protection, required checks, Pages Actions configuration, production deployment,
  smoke testing, monitoring ownership, and rollback rehearsal require repository-owner authority.
- The current correction path depends on someone monitoring GitHub issues; assign that owner.

## 9. Current Git/worktree posture

All authorized remediation exists as a dirty working tree on
`launch/aug1-directory-base`, still pointing at baseline commit `6f40dd80...`. Tracked modifications
include `.gitignore`, `README.md`, `paradisio_app/build.py`, client assets, requirements, and
`pv_master_unified.csv`; the legacy tracked `docs/paradisio_app/data/maps_parsed_v3.json` is deleted.
New paths include the workflow, issue template, audit records, semantic implementation/artifact,
vendored map assets, scripts, tests, tools, and this handover.

Because most additions are untracked, a plain `git diff` is incomplete. Review with:

```powershell
git status --short --untracked-files=all
git diff --stat
git diff
git ls-files --others --exclude-standard
```

Before staging, explicitly verify that no browser profile, cookie store, WhatsApp personal evidence,
`.venv`, or generated `release/` file appears. Stage intentionally by reviewed path; do not use a
blind `git add -A` until the legacy/evidence publication boundary is agreed.

## 10. Recommended next-agent sequence

1. Read this document, `AGENTS.md`, `06-change-log.md`, `07-verification-register.md`,
   `08-launch-checklist.md`, and `11-authority-tail-handoff.md`.
2. Run the complete deterministic verification sequence before editing.
3. Inspect the full tracked and untracked diff, with special attention to canonical-data manifests,
   ignored evidence, legacy `docs/`, and the CI workflow.
4. Perform one fresh desktop/mobile browser regression against `release/`.
5. Update any stale current-state documentation discovered during that review; preserve historical
   baseline reports as point-in-time evidence.
6. Present the owner with a concise residual-risk and file-scope review.
7. Obtain explicit decisions on catalog risk, legacy cleanup, correction monitoring, accessibility
   testing, release approval, and rollback ownership.
8. Only after approval: stage reviewed paths, commit, push the launch branch, open a pull request,
   inspect remote CI and its uploaded artifact, and record its commit/artifact identity.
9. Only after artifact approval: configure Pages for Actions, deploy the exact artifact, run
   production smoke tests, and retain rollback coverage.

## 11. Authority gates — do not cross autonomously

The following require explicit owner authorization:

- deleting legacy tracked material or rewriting history;
- choosing whether unknown/stale listings launch or are excluded;
- committing the candidate;
- pushing or opening/merging a pull request;
- changing branch protection or GitHub Pages settings;
- adding a deploy job or deploying any artifact;
- contacting businesses, sending WhatsApp messages, making calls, or submitting forms;
- using paid APIs or commercial datasets;
- announcing launch or accepting residual risk on the owner's behalf.

## 12. Release and rollback runbook

After authority is granted:

1. Freeze code and data; rerun all local gates.
2. Record branch, commit SHA, master CSV hash, semantic JSON hash, test count, profile/QR count, and
   release tree hash or archived artifact hash.
3. Push the launch branch and open a reviewed PR.
4. Require the remote `Launch readiness` workflow to pass.
5. Download and inspect the `paradisio-reduced-release` artifact; do not rebuild a different artifact
   for deployment.
6. Merge only the reviewed commit under the agreed branch controls.
7. Configure GitHub Pages to deploy the Actions artifact while preserving `/paradisio_app/` URLs.
8. Smoke test root, home/data load, search, representative filters, map, active/closed profiles,
   WhatsApp/Call/Maps link syntax, QR, correction link, sitemap, robots, direct refresh, and 404.
9. Record deployed commit, artifact identity, timestamp, tester, and results in the verification
   register.
10. If a critical smoke test fails, restore the prior known-good Pages artifact/commit and record the
    incident. Do not patch production ad hoc.

## 13. Documentation map

- `00-scope-and-methodology.md` — original audit rules and evidence standard.
- `01-system-inventory.md` — audited baseline inventory; historical counts.
- `02-audit-log.md` — chronological work record.
- `03-findings-register.md` — stable finding IDs and baseline evidence.
- `04-launch-gap-analysis.md` — baseline-to-launch gap analysis.
- `05-remediation-plan.md` — initiatives and acceptance criteria.
- `06-change-log.md` — every authorized local correction initiative.
- `07-verification-register.md` — mechanical and browser verification evidence.
- `08-launch-checklist.md` — current control checklist.
- `09-final-readiness-report.md` — original no-go and early candidate assessment; historical.
- `10-visual-product-critique.md` — desktop/mobile product and aesthetic assessment.
- `11-authority-tail-handoff.md` — owner-only decisions and release actions.
- `12-semantic-reenrichment-initiative.md` — taxonomy/evidence design.
- `13-aug1-release-candidate-handover.md` — authoritative current handover.
- `evidence/` — baseline and intermediate evidence.
- `docs/AUTOVISUALWHATSAPPCHECKIFIER.md` — WhatsApp visual audit specification.

## 14. Definition of ready for August 1

The reduced candidate is ready to go live only when:

- local and remote automated verification both pass on the exact candidate commit;
- a fresh representative desktop/mobile regression passes;
- the owner explicitly disposes of catalog and legacy-repository risks;
- the public artifact is confirmed to contain only allowlisted release files;
- Pages deploys the reviewed artifact rather than the legacy mixed `docs/` tree;
- a named person monitors corrections and launch health;
- production smoke tests pass; and
- a tested rollback path and authorized rollback owner are present.

Until those conditions are recorded, describe the workspace as a **mechanically verified local
release candidate**, not a deployed or finally approved production release.
