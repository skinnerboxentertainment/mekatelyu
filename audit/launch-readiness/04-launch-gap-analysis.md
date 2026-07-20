# Launch Gap Analysis

Status: Assessment complete; remediation not started

| Domain | Current status | Evidence status | Target state |
|---|---|---|---|
| Build reproducibility | Pass with gap | Clean rebuild matches committed paths/content except timestamp; procedure not automated | Clean, documented, repeatable build |
| Core functionality | Finding | Search/detail render; payment, posting, localization, and closed-listing journeys fail launch criteria | Critical journeys pass without console/network errors |
| Responsive design | Finding | No 390 px overflow; fixed controls overlap primary CTA | Usable at representative mobile and desktop sizes |
| Accessibility | Finding | Missing landmarks/labels/state, weak focus treatment, no reduced-motion rule, and sampled contrast failures; manual keyboard traversal remains | No critical barriers; fundamentals and keyboard use verified |
| Data quality | Finding | Invalid routes, malformed contacts, stale/duplicate/out-of-scope records, and demo classifieds | Defined invariants and lifecycle rules pass; limitations disclosed |
| Security and privacy | Blocker | Public invoice/admin data, unenforceable privileged modes, and undisclosed third-party form/analytics processing | No exposed sensitive operational data or unsafe trust assumptions |
| Dependency health | Finding | Range-only Python requirements; no lock/hashes; CDN assets lack SRI/fallback | Dependencies known, reproducible, integrity-controlled, and reviewed |
| Performance | Finding | Large duplicate catalog payload; constrained measurement pending | Launch-relevant pages meet defined budgets |
| SEO and sharing | Finding | Canonical/social/indexation controls incomplete | Metadata, canonical behavior, and discoverability are intentional |
| Publication boundary | Finding | Pages serves a mixed 2,538-file product/data/research/working tree | Allowlisted minimal release artifact only |
| Operations | Finding | Live Pages from unprotected `master:/docs`; no CI/staging/custom 404/verified rollback | Protected deployment, rollback, monitoring, feedback, and ownership documented |
| Legal/trust content | Finding | Payment promise, verification badges, analytics/privacy, and third-party data claims need review | Claims, attribution, privacy, and user expectations are supportable |
