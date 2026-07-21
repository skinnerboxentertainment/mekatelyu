# Launch Checklist

Status values: Not assessed, In progress, Pass, Finding, Blocked, Deferred.

| Control | Status | Evidence / finding |
|---|---|---|
| Production build is reproducible from a clean checkout | Pass | Isolated build; 2,500 paths; timestamp-only variance |
| Published output corresponds to reviewed source and data | Pass locally | Minimal reproducible `release/` artifact; deployment migration pending |
| Critical visitor journeys pass | Pass locally | Search/filter/map/detail/QR/closed-state browser regression |
| Claim, premium, payment, invoice, and dashboard expectations are accurate and safe | Pass by scope | Surfaces absent from reduced candidate; legacy repository cleanup remains |
| Mobile and desktop layouts pass representative viewport checks | Pass locally | 1440×1000, 390×844, 320×568 |
| Keyboard and accessibility fundamentals pass | In progress | Semantics/names/focus/motion/contrast improved; manual screen-reader/keyboard lab remains |
| No launch-blocking console or network failures | Pass locally | Maps self-hosted; CSP/failure state; browser journeys pass |
| Data invariants and disclosure requirements pass | In progress | Critical route/status checks pass; stale/duplicate/unknown content review remains |
| Secret and sensitive-data review passes | Finding | PRIV-001, REPO-001; limited strong-token scan found no confirmed secret |
| External links and deep links are valid | Pass locally | Internal refs zero broken; HTTP refs zero; exhaustive live endpoint health not run |
| Performance baseline is acceptable | Pass locally | 5.5 KB shell + 508 KB directory asset; fixed budgets pass |
| SEO, metadata, robots, and sharing behavior are intentional | Pass locally | Canonical/OG/CSP all pages; sitemap/robots/root 404 |
| Deployment and rollback procedure is documented and tested | Finding | OPS-001; production source confirmed, rollback unverified |
| Monitoring and user-feedback path exist | In progress | Privacy-safe GitHub correction template added; operational ownership pending |
| All blocker/high findings are verified closed or explicitly accepted | Finding | Legacy privacy/publication and catalog-governance work remain |
| Public artifact contains only intended release files | Pass locally | Allowlisted generated release; production still uses legacy Pages source |
| Branch/release controls prevent unreviewed production changes | Finding | CI prepared; `master` protection and Pages migration require authority |
| Final launch decision is recorded | Finding | Audit recommendation: no-go until required conditions are verified |
