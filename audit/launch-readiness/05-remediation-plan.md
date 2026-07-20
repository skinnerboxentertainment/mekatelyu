# Remediation Plan

No remediation initiative is approved during the read-only baseline. Initiatives will be added only after a gap is reproduced and linked to one or more finding IDs.

| Initiative | Findings | Priority | Effort | Dependencies | Acceptance criterion | Status |
|---|---|---|---|---|---|---|
| INIT-001 Payment launch control | PAY-001 | P0 | Medium | Verified SINPE/owner details; fulfilment/refund decision | Payment disabled until end-to-end verified | Implemented by scope removal |
| INIT-002 Remove public privileged data/modes | PRIV-001, AUTH-001, SEC-001 | P0 | Medium–High | Decide private operations platform | Public artifact contains no invoice/admin data | Candidate passes; legacy cleanup pending |
| INIT-003 Repair posting channel | FUNC-001 | P0 | Small | Monitored production address/form decision | Test post received and processed | Feature removed from launch |
| INIT-004 Contact/status validation | DATA-001, DATA-002 | P0 | Medium | Business rules for inferred WhatsApp and closed records | All routes/status CTAs pass invariants | Verified locally |
| INIT-005 Complete localization | I18N-001 | P1 | Medium | Supported-language decision | Representative journeys fully translate/persist | Unsupported controls removed |
| INIT-006 Resolve fixed mobile UI | MOB-001 | P1 | Small | Decide whether modes ship | No overlap at supported widths | Verified locally |
| INIT-007 Establish CI release gate | QA-001 | P1 | Medium | GitHub Actions/deployment decision | Build, invariants, links, and browser smoke pass in CI | Implemented locally; remote run pending |
| INIT-008 Accessibility hardening | A11Y-001 | P1 | Medium | Supported browser/device matrix | Automated + keyboard/screen-reader checklist passes | In progress |
| INIT-009 Performance budget | PERF-001 | P1 | Medium | Catalog-loading architecture decision | Defined constrained-mobile budget passes | Local budgets pass |
| INIT-010 Search/social metadata | SEO-001 | P2 | Medium | Canonical production URL | Canonical, sitemap, robots, sharing validated | Verified locally |
| INIT-011 Browser-policy hardening | SEC-001 | P1 | Medium | CDN/self-hosting decision | CSP/referrer and safe rendering verified | Verified locally |
| INIT-012 Documentation source of truth | DOC-001 | P2 | Small | Canonical metrics generation | Counts/as-of dates are consistent | Verified locally |
| INIT-013 Privacy and data-handling controls | PRIV-002 | P0 | Medium | Owner/legal policy decisions; processor review | Collection points disclose reviewed policy and minimize data | Collection removed from launch |
| INIT-014 Normalize and monitor external links | EXT-001 | P1 | Medium | Endpoint sampling and redirect policy | External link check passes on release | Launch scheme gate passes |
| INIT-015 Controlled Pages release/rollback | OPS-001 | P1 | Medium | Branch protection and deployment strategy | Staged release and rollback drill pass | Awaiting authority |
| INIT-016 Minimal public artifact | PUB-001, PRIV-001 | P0 | Medium | Decide public routes/assets; deployment workflow | Only allowlisted product files are publicly reachable | Candidate verified; deployment pending |
| INIT-017 Catalog governance and cleanup | DATA-001, DATA-002, DATA-003 | P0 | High | Geographic/freshness/contact/status policy | Data-invariant report passes with reviewed exceptions | Critical routes pass; content review remains |
| INIT-018 Production classifieds lifecycle | FUNC-001, CLASS-001 | P0 | Medium–High | Decide whether classifieds launch Aug 1; moderation owner | No fictional/expired ad is presented as active | Feature removed from launch |
| INIT-019 Reproducible dependencies | SEC-002 | P1 | Medium | Self-hosting/SRI and Python lock strategy | Clean build uses reviewed immutable dependencies | Verified locally |
| INIT-020 Repository retention and secret review | REPO-001 | P1 | Medium | Decide history-remediation scope | Public repo contains no unnecessary session/log data; secret scan passes | Awaiting authority |
| INIT-021 Semantic re-enrichment and discovery coverage | DATA-003 | P0 | High | Local CID/source evidence; taxonomy policy | 771 records receive provenance-backed groups/tags; discovery invariants pass; ambiguous rewrites remain review-only | In progress locally |

## Aug 1 critical path

The remaining window is 12 calendar days from this audit date. This sequence assumes remediation authorization and named owners; it is a planning recommendation, not an implemented schedule.

| Date | Exit condition |
|---|---|
| Jul 20–21 | Freeze feature scope; decide whether payment, owner/admin modes, claims, and classifieds launch at all; assign every P0 owner |
| Jul 21–23 | Remove/disable unsafe surfaces; establish minimal publish artifact; correct placeholder routes and highest-risk catalog defects |
| Jul 24 | Independent P0 verification: clean build, privacy/public-route probe, payment/contact tests, data invariants |
| Jul 25–27 | P1 work: mobile/accessibility, localization decision, dependencies, external links, CI and branch/release controls |
| Jul 28 | Code and catalog freeze; produce exact release-candidate artifact and content manifest |
| Jul 29 | Full regression, representative devices, link/dependency check, rollback drill, operational runbook rehearsal |
| Jul 30 | Formal go/no-go review; all blockers/highs verified closed or explicitly removed from launch scope |
| Jul 31 | Contingency only; no unreviewed features or bulk data changes |
| Aug 1 | Deploy the approved immutable artifact, smoke test, monitor, and retain rollback authority |

If the team cannot staff this sequence immediately, the safer launch is a reduced directory-only surface: no payment, no public admin/owner simulation, no claim form, and no classifieds until their controls are ready.

## Initiative template

### `INIT-NNN` — Title

- Related findings:
- Objective:
- Proposed scope:
- Out of scope:
- Dependencies and decisions:
- Risks:
- Estimated effort:
- Acceptance criteria:
- Verification plan:
- Status:
# WhatsApp identity-verification initiative

- Specification: `docs/AUTOVISUALWHATSAPPCHECKIFIER.md`.
- Build a resumable local review queue and append-only evidence ledger.
- Pilot browser/vision inspection on six routes without sending messages.
- Keep the 106 established routes intact during review.
- Place all ambiguous identity decisions and every production-data patch at the authority tail.
- Treat the checker as QA infrastructure rather than an August 1 launch blocker.
